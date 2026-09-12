# Western Union Check Downloading Automation Guide

This guide outlines automated strategies and reference implementations for logging into Western Union, iterating through the checks table, opening check images/PDFs, and saving each file locally as `Check # <XXXX>.pdf`.

---

## Strategy 1: Python + Playwright Automation (Recommended ⭐)

[Playwright](https://playwright.dev/python/) is the most reliable tool for this task because it handles dynamic web tables, popup windows, and direct file download interception without needing OS print/save dialogs.

### Prerequisites
Install Playwright and Chromium browser binary:
```bash
pip install playwright
playwright install chromium
```

### Reference Implementation Script (`automate_wu_checks.py`)

```python
import os
import time
from playwright.sync_api import sync_playwright

# Folder where check images/PDFs will be saved
DOWNLOAD_DIR = os.path.abspath("./western_union_checks")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def run_automation():
    with sync_playwright() as p:
        # Launch browser in visible (headful) mode for manual login / 2FA
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        context = browser.new_context(
            accept_downloads=True,
            viewport=None
        )
        page = context.new_page()

        # Step 1: Navigate to Western Union Portal
        print("Navigating to Western Union Portal...")
        page.goto("https://www.westernunion.com/")

        # Step 2: Manual Login & 2FA Prompt
        print("\n=======================================================")
        print("PLEASE LOG IN TO WESTERN UNION MANUALLY IN THE BROWSER.")
        print("NAVIGATE TO THE 'CHECKS' PAGE / TABLE.")
        print("Press ENTER in this terminal once you are on the Checks page.")
        print("=======================================================\n")
        input("Press Enter to start downloading checks...")

        # Step 3: Locate the Check Rows Table
        # Adjust selector based on actual page structure (e.g., "table tbody tr" or ".check-row")
        row_selector = "table tbody tr"
        rows = page.locator(row_selector).all()
        total_checks = len(rows)
        print(f"Found {total_checks} check records in table.")

        for index in range(total_checks):
            # Re-fetch row list in case of DOM re-renders
            current_row = page.locator(row_selector).nth(index)
            
            # Extract Check Number (update column selector as needed)
            check_number_el = current_row.locator("td:nth-child(2)") # Adjust column index
            check_number = check_number_el.inner_text().strip() if check_number_el.count() > 0 else f"RECORD_{index+1}"
            
            # Clean filename
            safe_check_no = "".join([c for c in check_number if c.isalnum() or c in ("-", "_", " ")])
            target_filename = os.path.join(DOWNLOAD_DIR, f"Check # {safe_check_no}.pdf")

            print(f"[{index+1}/{total_checks}] Processing Check #{safe_check_no}...")

            # Skip if already downloaded
            if os.path.exists(target_filename):
                print(f"  --> Already downloaded: {target_filename}. Skipping.")
                continue

            # Step 4: Click Check Icon & Capture Popup / Download
            icon_button = current_row.locator("button, a, .icon-view").first

            try:
                # Handle case where clicking opens a new tab or triggers a download
                with context.expect_page(timeout=10000) as new_page_info:
                    icon_button.click()
                
                popup_page = new_page_info.value
                popup_page.wait_for_load_state("domcontentloaded")

                # Inside Popup: Click Print / Save Button
                print_button = popup_page.locator("button:has-text('Print'), button:has-text('Save'), #printBtn").first
                
                with popup_page.expect_download(timeout=15000) as download_info:
                    print_button.click()
                
                download = download_info.value
                download.save_as(target_filename)
                print(f"  --> Saved: {target_filename}")

                # Close popup page and return to main window
                popup_page.close()

            except Exception as err:
                print(f"  [WARNING] Direct popup download failed for Check #{safe_check_no}: {err}")
                print("  Attempting fallback screenshot capture...")
                # Fallback: Capture screenshot of viewer element if PDF download is blocked
                try:
                    if 'popup_page' in locals() and not popup_page.is_closed():
                        popup_page.screenshot(path=target_filename.replace(".pdf", ".png"))
                        popup_page.close()
                except Exception as ss_err:
                    print(f"  [ERROR] Fallback screenshot failed: {ss_err}")

            time.sleep(1) # Polite delay between requests

        print("\n🎉 All checks processed successfully!")
        browser.close()

if __name__ == "__main__":
    run_automation()
```

---

## Strategy 2: Tampermonkey Userscript (In-Browser Solution)

If running external Python scripts is restricted, you can inject a custom JavaScript button into Western Union using Tampermonkey.

### Features:
- Adds a **"🚀 Bulk Download All Checks"** floating button on the Western Union checks page.
- Parses all rows, fetches images directly via `window.fetch()`, and triggers browser downloads natively as `Check # <XXXX>.pdf`.

```javascript
// ==UserScript==
// @name         Western Union Bulk Check Downloader
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Bulk download scanned checks from Western Union list
// @match        https://*.westernunion.com/*
// @grant        GM_download
// ==/UserScript==

(function() {
    'use strict';

    window.addEventListener('load', function() {
        const btn = document.createElement('button');
        btn.innerHTML = '🚀 Bulk Download All Checks';
        btn.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 99999; padding: 12px 20px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3);';
        document.body.appendChild(btn);

        btn.addEventListener('click', async function() {
            const rows = document.querySelectorAll('table tbody tr');
            alert(`Found ${rows.length} check records. Download starting...`);

            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const checkNoEl = row.querySelector('.check-number, td:nth-child(2)');
                const checkNo = checkNoEl ? checkNoEl.innerText.trim() : `Check_${i+1}`;
                const iconBtn = row.querySelector('button, a, .icon-view');

                if (iconBtn) {
                    iconBtn.click();
                    await new Promise(r => setTimeout(r, 2000)); // Wait for modal/popup
                }
            }
        });
    });
})();
```

---

## Strategy 3: DevTools Network API Extraction (Fastest)

1. Press `F12` in Chrome/Edge to open **DevTools** ➔ **Network** tab.
2. Click on one check icon manually.
3. Observe the API call sent (e.g. `GET /api/v1/checks/document?id=100452`).
4. If Western Union returns a direct PDF stream or JSON with image URL, copy your session Cookie / Token and run a single Python `requests` loop:

```python
import requests

cookies = { ... } # Copy from DevTools
headers = { ... }

check_ids = ["100451", "100452", "100453"]
for cid in check_ids:
    res = requests.get(f"https://www.westernunion.com/api/v1/checks/document?id={cid}", cookies=cookies, headers=headers)
    with open(f"Check # {cid}.pdf", "wb") as f:
        f.write(res.content)
```

---

## Troubleshooting & Best Practices

1. **Anti-Automation & Rate Limiting**: Include a 1-2 second delay (`time.sleep(1.5)`) between check downloads to avoid triggering Western Union session timeouts.
2. **Duplicate Protection**: Always check `os.path.exists(target_filename)` before clicking so you can safely resume interrupted downloads.
3. **Session Expiration**: Log in fresh before running Playwright in headful mode.
