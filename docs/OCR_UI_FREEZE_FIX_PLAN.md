# Fix: OCR Background Processing Causing UI Freeze on Module Navigation

## Background & Root Cause

When a customer's **Inbox** receives a file (via portal upload or inbound email), the system runs a full OCR + classification pipeline (`classify_and_rename_tax_document`) to identify the form type and rename the file accordingly.

The **root cause of the UI freeze** when navigating between modules is:

> **FastAPI `BackgroundTasks` run synchronous functions on the uvicorn event loop thread.** `classify_and_rename_tax_document` is a **heavy synchronous function** (Google Vision OCR, `fitz` PDF-to-image rendering, multiple S3 calls, DB writes). While it runs, the single-worker uvicorn event loop is **blocked** — it cannot process any new HTTP requests, including the navigation API calls triggered by the dashboard UI.

### Proof of the Block Chain

```
[Inbound email / portal upload]
  → background_tasks.add_task(classify_and_rename_tax_document, ...)
      ↳ _ocr_pdf_to_text_for_classification(file_key)
          ↳ S3 download (blocking)
          ↳ fitz.open() → page.get_pixmap() [CPU heavy]
          ↳ Google Vision API call (blocking network I/O)
      ↳ S3 copy_object + delete_object (blocking)
      ↳ DB INSERT/UPDATE (blocking)
      ↳ recalculate_tax_docs_status() (blocking)
  → ENTIRE EVENT LOOP BLOCKED for ~5–30s per file
```

The Dockerfile confirms **a single uvicorn worker** (`uvicorn app:app ...` — no `--workers` flag), making this a **single-threaded bottleneck**.

---

## Proposed Changes

---

### 1 — Backend: Wrap Background Tasks in a Thread Pool Executor

**The minimal, safest fix.** FastAPI's `run_in_threadpool` (which wraps `asyncio.run_in_executor`) moves synchronous functions off the event loop into a thread pool. We need to replace all `background_tasks.add_task(classify_and_rename_tax_document, ...)` callsites with an async wrapper that uses `run_in_threadpool`.

#### [MODIFY] [app.py](file:///d:/VRTServices/app.py)

**Change 1 — Add async wrapper** (near the `classify_and_rename_tax_document` definition, ~line 13013):

Add a thin async wrapper function just below `classify_and_rename_tax_document`:

```python
async def classify_and_rename_tax_document_async(
    customer_id: int, file_key: str, original_filename: str = "", tax_year: int = None
):
    """
    Async wrapper that runs the blocking OCR+classify pipeline in a thread pool
    so the uvicorn event loop is never blocked.
    """
    from fastapi.concurrency import run_in_threadpool
    await run_in_threadpool(
        classify_and_rename_tax_document,
        customer_id, file_key, original_filename, tax_year
    )
```

**Change 2 — Replace `background_tasks.add_task` callsites** (4 locations):

| Location | Line | Change |
|---|---|---|
| Portal upload (`/api/portal/...`) | ~4005 | `classify_and_rename_tax_document` → `classify_and_rename_tax_document_async` |
| Staff storage upload (`/api/customers/{id}/storage/upload`) | ~7153 | same |
| Manual classify API (`/api/tax-docs/classify`) | ~13713 | same |
| Scan existing API (`/api/tax-docs/scan-existing`) | ~13776 | same |

> **Note:** `process_inbound_post_processing` (~line 12184) calls `classify_and_rename_tax_document` **synchronously** inside itself, and it is already dispatched as a background task. However since it too is sync, it still runs on the event loop thread. We must also wrap it:

**Change 3 — Add async wrapper for `process_inbound_post_processing`** (~line 12576):

```python
async def process_inbound_post_processing_async(...all args...):
    from fastapi.concurrency import run_in_threadpool
    await run_in_threadpool(process_inbound_post_processing, ...all args...)
```

And update the `background_tasks.add_task` call at line ~12576 to use the new async wrapper.

---

### 2 — Backend: Add a Configurable Thread Pool Limit

By default, Python's `asyncio` executor is unbounded. If many inbound emails arrive simultaneously, many OCR tasks could spin up and consume all CPU/memory. Add a bounded thread pool on startup:

#### [MODIFY] [app.py](file:///d:/VRTServices/app.py)

Near app startup (top of file, after imports):

```python
import concurrent.futures
import asyncio

# Limit OCR background tasks to avoid resource exhaustion
_OCR_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="ocr-worker")

@app.on_event("startup")
async def configure_event_loop_executor():
    loop = asyncio.get_event_loop()
    loop.set_default_executor(_OCR_THREAD_POOL)
```

> This ensures at most 3 simultaneous OCR operations run concurrently, preventing memory spikes from parallel fitz + Google Vision calls.

---

### 3 — Backend: Add OCR Result Caching (de-duplicate repeated calls)

When multiple files arrive in the same email, or when `scan-existing` is triggered for an already-classified file, the OCR pipeline re-runs unnecessarily. Add a **simple in-memory LRU cache** keyed on `(file_key, file_size)`.

#### [MODIFY] [app.py](file:///d:/VRTServices/app.py)

Above `_ocr_pdf_to_text_for_classification`:

```python
import functools

@functools.lru_cache(maxsize=128)
def _cached_ocr_result(file_key: str, file_size_hint: int) -> str:
    """LRU cache for OCR text — keyed on file_key + size to avoid stale hits."""
    return _ocr_pdf_to_text_for_classification.__wrapped__(file_key)
```

Modify `_ocr_pdf_to_text_for_classification` to populate/check this cache after the S3 `get_object` call (once file size is known).

---

### 4 — Backend: Limit PDF Pages OCR'd

Currently OCR processes `min(3, len(doc))` pages. For large bank statement PDFs, page 1 alone is sufficient to determine form type. Reduce to **first page only** for the classification pipeline (not the full extraction pipeline):

#### [MODIFY] [app.py](file:///d:/VRTServices/app.py)

In `_ocr_pdf_to_text_for_classification` at line ~12818:

```python
# Change:
for page_idx in range(min(3, len(doc))):
# To:
for page_idx in range(min(1, len(doc))):   # Only page 1 needed for classification
```

This alone can **cut OCR time by 2–3x** for multi-page documents.

---

### 5 — Frontend: Non-blocking Navigation During OCR Processing

Even with the thread pool fix, if a user immediately navigates to a module that polls the server (e.g., loads tax docs), the navigation fetch may take slightly longer. Add a **frontend toast/status indicator** so the user knows OCR is processing in the background, rather than experiencing a silent freeze.

#### [MODIFY] [dashboard.html](file:///d:/VRTServices/templates/dashboard.html)

After the upload success response is received (the existing code already shows `alert(✅ ... OCR processing started.)`), replace the `alert()` call with a **toast notification** that doesn't block the UI. This prevents the `alert()` dialog from also stalling navigation.

Update `reClassifyTaxDoc` (~line 8578) and `scanExistingTaxDocs` (~line 8637):

```js
// Replace:
alert(`✅ ${data.message} — OCR processing started.`);
// With:
showToast(`✅ ${data.message} — OCR classification is running in the background.`, 'success');
```

Add a lightweight `showToast(message, type)` helper to the dashboard JS that renders a non-blocking bottom-right notification.

---

### 6 — Dockerfile: Add `--workers 2` to uvicorn (Optional but recommended)

Running with a single worker means any lingering synchronous code (even outside of OCR) can block all requests. Adding a second worker provides a fallback:

#### [MODIFY] [Dockerfile](file:///d:/VRTServices/Dockerfile)

```dockerfile
# Change:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
# To:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--workers", "2"]
```

> [!WARNING]
> With multiple workers, any **in-memory state** (e.g., `LAST_INBOUND_DEBUG`, `_OCR_THREAD_POOL`, module-level caches) will not be shared between workers. Review global state before enabling this.

---

## Priority Order

| # | Change | Impact | Risk | Effort |
|---|---|---|---|---|
| 1 | Wrap classify in `run_in_threadpool` | 🔴 Critical – fixes the freeze | Low | 30 min |
| 2 | Bounded thread pool executor | 🟠 High – prevents resource spikes | Low | 15 min |
| 3 | Limit OCR to page 1 only | 🟠 High – 2–3x faster OCR | Very Low | 5 min |
| 4 | Frontend toast instead of `alert()` | 🟡 Medium – removes UI block | Very Low | 20 min |
| 5 | OCR result LRU cache | 🟡 Medium – avoids redundant work | Low | 30 min |
| 6 | Uvicorn `--workers 2` | 🟢 Low – defense-in-depth | Medium | 5 min |

---

## Verification Plan

### Automated
- None currently (no test suite). A scratch test script can simulate a concurrent file upload + navigation fetch and measure response latency.

### Manual Verification
1. Upload a multi-page PDF to a customer Inbox via the portal.
2. **Immediately** navigate between dashboard modules.
3. Confirm there is no freeze — navigation API calls return within `< 500ms`.
4. Confirm the file is eventually renamed in S3 and appears in the Tax Doc Tracking table.
5. Check server logs to confirm `[TAX CLASSIFY]` logs appear from a thread, not the main loop.

