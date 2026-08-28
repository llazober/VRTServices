# Check Image Processing & GL Account Matching Architecture

## Overview
This document outlines the design, workflow, and troubleshooting rules for processing check images (PDFs / scans) and matching check details against bank statements and `ClientTransactionHistory` GL rules.

---

## Processing Flow

```
User uploads Check Image (.pdf / .png / .jpg)
       │
       ▼
1. Backend Endpoint: POST /process-checks (app.py)
   ├── Saves temporary file
   └── Calls extract_check_images() in extractor.py
       │
       ▼
2. Check OCR Extraction (extractor.py)
   ├── Uses Google Cloud Vision API
   ├── Extracts: check_number, payee, business_name, amount
   └── Calls match_gl_account(raw_desc=f"{payee} {check_number}")
       └── Returns 4-tuple: (acct_num, acct_name, conf, matched_desc)
       │
       ▼
3. Frontend UI Matching (templates/index.html - handleCheckPdfUpload)
   ├── Matches check_number / targetDigits OR exact amount against currentResult.transactions
   ├── Updates transaction description to payee
   ├── Updates tx.account (Account Number) to matched GL rule from ClientTransactionHistory
   └── Calls displayResults(currentResult) to instantly refresh table
```

---

## Crucial Implementation & Debugging Gotchas

### 1. `match_gl_account` Return Signature
- `match_gl_account()` returns a **4-tuple**: `(acct_num, acct_name, conf, matched_desc)`.
- When invoking in `extract_check_images()`, **always unpack 4 values**:
  ```python
  acct_num, acct_name, conf, _matched_desc = match_gl_account(...)
  ```
  *(Unpacking only 3 values will cause a silent `ValueError: too many values to unpack` that empties check extraction results).*

### 2. UI Table Column Filtering
- `matched_description` is internal transaction metadata used to populate the CSV `Reference` field for bank statements when check numbers are absent.
- `matched_description` **must be included in the hidden key filter** in `templates/index.html` (alongside `account_name`, `match_confidence`, `match_source`) so it does not render as a visible column header in the table.

### 3. Asynchronous UI Handler & Network Pre-fetches
- Do **NOT** add blocking pre-fetch HTTP requests (like `fetch('/api/clients/history')`) inside `handleCheckPdfUpload()` before launching `/process-checks`.
- The backend `/process-checks` endpoint automatically fetches client history rules directly from the database server-side.
- Always call `showAlert('📷 Processing check file(s)...', 'info')` **immediately at the top** of `handleCheckPdfUpload()` for 0ms visual feedback.

### 4. File Input Event Triggering
- Use standard native HTML `<label for="uploadCheckImagesInput">` tags for triggering file pickers without programmatic `.click()` popup blocking.
- Reset `input.value = ''` immediately upon capturing `input.files` to ensure selecting duplicate files always triggers the `onchange` event cleanly.

---

## File Map
- `extractor.py`: `extract_check_images()`, `match_gl_account()`, `run_extraction()`
- `app.py`: `@app.post("/process-checks")`, `@app.post("/process-checks-from-do")`
- `templates/index.html`: `handleCheckPdfUpload()`, `processDoChecks()`, `displayResults()`
- `matching_engine.py`: History rule regex & pattern matching engine
