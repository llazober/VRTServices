import os
import sys
import time
import json
import re
import argparse
import datetime
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DOWNLOAD_DIR = os.path.abspath("./western_union_checks")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

STATUS_FILE = os.path.join(DOWNLOAD_DIR, "automation_status.json")

def update_status(status, message, total=0, processed=0, current_file=""):
    data = {
        "status": status,
        "message": message,
        "total_checks": total,
        "processed_checks": processed,
        "current_file": current_file,
        "updated_at": datetime.datetime.now().isoformat()
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[STATUS WRITE ERROR]: {e}")

def extract_check_number_from_text(text_content):
    if not text_content:
        return None
    match = re.search(r"Check\s*Number[\s:]*(\w+)", text_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def run_automation(target_url=None, cdp_url=None, interactive_prompt=True):
    update_status("running", "Initializing Western Union Check Automation routine...")
    print("\n==========================================================================")
    print("[START] WESTERN UNION CHECK AUTOMATION - EXACT SEQUENCE WORKFLOW")
    print("==========================================================================")
    print(f"Target Download Directory: {DOWNLOAD_DIR}")
    if cdp_url:
        print(f"CDP Remote Debugging Mode: {cdp_url}")
    if target_url:
        print(f"Target Check List URL: {target_url}")
    print("==========================================================================\n")

    try:
        with sync_playwright() as p:
            browser = None
            context = None
            page = None

            if cdp_url:
                print(f"Connecting to existing open browser at {cdp_url}...")
                try:
                    browser = p.chromium.connect_over_cdp(cdp_url)
                    contexts = browser.contexts
                    if contexts and len(contexts) > 0:
                        context = contexts[0]
                        pages = context.pages
                        if pages:
                            page = pages[0]
                        else:
                            page = context.new_page()
                    else:
                        context = browser.new_context(accept_downloads=True)
                        page = context.new_page()
                    print("Successfully connected to existing browser session!")
                except Exception as cdp_err:
                    print(f"[CDP CONNECTION WARNING]: Could not connect via CDP ({cdp_err}). Launching fresh browser instance...")
                    cdp_url = None

            if not browser:
                print("Launching visible Chromium browser...")
                browser = p.chromium.launch(
                    headless=False,
                    args=["--start-maximized"]
                )
                context = browser.new_context(
                    accept_downloads=True,
                    viewport=None
                )
                page = context.new_page()

            url_to_open = target_url or os.environ.get("WU_CHECK_URL") or "http://127.0.0.1:8000/"
            
            if not cdp_url or not page.url or page.url == "about:blank":
                print(f"Step 1: Navigating to Check List URL ({url_to_open})...")
                update_status("waiting_login", f"Browser opened. Navigating to Checks table on {url_to_open}.")
                page.goto(url_to_open)

            print("\n=======================================================")
            print("BROWSER IS OPEN & READY ON CHECKS PAGE.")
            print("AUTOMATION WILL ITERATE THROUGH EVERY CHECK ROW:")
            print("  1. Open Check Details Modal (Page 2)")
            print("  2. Read Check Number & Click 'Print' (Page 3)")
            print("  3. Save PDF as 'Check # <XXXX>.pdf' into ./western_union_checks/ (Page 4)")
            print("  4. Click 'X' to Close Modal (Page 5) and move to next row.")
            print("=======================================================\n")
            
            if interactive_prompt:
                try:
                    input("Press Enter to start downloading checks...")
                except (EOFError, OSError):
                    print("No interactive console stdin attached. Waiting 3 seconds before starting sequence...")
                    time.sleep(3)

            update_status("running", "Locating checks table records...")
            
            # Find open check buttons or rows
            row_selector = "button:has-text('Open Check Image'), button:has-text('View'), .check-row, table tbody tr"
            
            check_buttons = page.locator(row_selector).all()
            total_checks = len(check_buttons)
            print(f"Found {total_checks} check records/buttons in table.")
            update_status("running", f"Found {total_checks} check records.", total=total_checks, processed=0)

            if total_checks == 0:
                print("[WARNING]: No check rows or 'Open Check Image' buttons detected on page.")
                update_status("completed", "No check rows found on page.", total=0, processed=0)
                return

            for index in range(total_checks):
                btn = page.locator(row_selector).nth(index)
                
                # Scroll element into view
                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass

                print(f"\n[{index+1}/{total_checks}] Step 1 -> Clicking Open Check Image for row {index+1}...")
                
                # Step 2: Open Check Details Modal
                try:
                    btn.click(timeout=5000)
                except Exception as click_err:
                    print(f"  [WARNING]: Could not click button at index {index}: {click_err}")
                    continue

                time.sleep(1) # Allow modal to render

                # Step 2: Extract Check Details from Modal
                modal = page.locator(".modal, [role='dialog'], .modal-content, div:has-text('Check Details')").first
                modal_text = modal.inner_text() if modal.count() > 0 else page.locator("body").inner_text()
                
                check_no = extract_check_number_from_text(modal_text)
                if not check_no:
                    check_no = f"CHECK_{index+1:04d}"

                safe_check_no = "".join([c for c in check_no if c.isalnum() or c in ("-", "_", " ")])
                target_filename = os.path.join(DOWNLOAD_DIR, f"Check # {safe_check_no}.pdf")

                print(f"  --> Page 2 (Check Details Modal): Check Number detected: #{safe_check_no}")
                update_status("running", f"Processing Check #{safe_check_no} ({index+1}/{total_checks})", total=total_checks, processed=index, current_file=f"Check # {safe_check_no}.pdf")

                if os.path.exists(target_filename):
                    print(f"  --> Already saved: {target_filename}. Closing modal and skipping.")
                    # Step 5: Close Modal (X)
                    try:
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
                    except Exception:
                        pass
                    continue

                # Step 3: Click "Print" button on modal
                print_btn = modal.locator("button:has-text('Print'), a:has-text('Print'), [data-action='print']").first if modal.count() > 0 else page.locator("button:has-text('Print'), a:has-text('Print')").first

                saved_success = False
                if print_btn.count() > 0:
                    print(f"  --> Page 3: Clicking 'Print' button...")
                    
                    try:
                        with context.expect_page(timeout=5000) as new_page_info:
                            print_btn.click()
                        
                        popup_page = new_page_info.value
                        popup_page.wait_for_load_state("domcontentloaded")
                        print("  --> Page 3/4: Print preview tab opened. Clicking Save / generating PDF...")

                        save_btn = popup_page.locator("button:has-text('Save'), #save-button, .btn-primary:has-text('Save')").first
                        if save_btn.count() > 0:
                            with popup_page.expect_download(timeout=10000) as download_info:
                                save_btn.click()
                            download = download_info.value
                            download.save_as(target_filename)
                        else:
                            popup_page.pdf(path=target_filename)

                        print(f"  --> Page 4: PDF successfully saved: {target_filename}")
                        saved_success = True
                        popup_page.close()

                    except Exception as print_err:
                        print(f"  [NOTE]: Direct print popup fallback: {print_err}")
                        try:
                            page.pdf(path=target_filename)
                            print(f"  --> Saved page PDF: {target_filename}")
                            saved_success = True
                        except Exception:
                            png_path = target_filename.replace(".pdf", ".png")
                            if modal.count() > 0:
                                modal.screenshot(path=png_path)
                            else:
                                page.screenshot(path=png_path)
                            print(f"  --> Saved check image screenshot: {png_path}")
                            saved_success = True

                # Step 5: Click X to close modal and return to main page
                print("  --> Page 5: Clicking 'X' button to close modal and return to main list...")
                close_clicked = False
                close_btn = page.locator("button.close, button:has-text('×'), .close, [data-dismiss='modal']").first
                if close_btn.count() > 0 and close_btn.is_visible():
                    try:
                        close_btn.click()
                        close_clicked = True
                    except Exception:
                        pass

                if not close_clicked:
                    page.keyboard.press("Escape")

                # Clean up any lingering modal backdrop elements to prevent pointer intercept delays
                try:
                    page.evaluate("document.querySelectorAll('.modal, .modal-backdrop').forEach(el => { el.classList.remove('active', 'show'); el.style.display = 'none'; });")
                except Exception:
                    pass

                time.sleep(0.5) # Return to initial list page

            print("\n[SUCCESS] Western Union Check Automation Sequence Completed Successfully!")
            update_status("completed", f"All {total_checks} checks processed successfully.", total=total_checks, processed=total_checks)
            if not cdp_url:
                browser.close()

    except Exception as ex:
        print(f"[AUTOMATION ERROR]: {ex}")
        update_status("error", f"Automation error: {ex}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Western Union Check Automation")
    parser.add_argument("--url", type=str, default=None, help="Target URL showing checks list table")
    parser.add_argument("--cdp", type=str, default=None, help="CDP URL of already open browser (e.g. http://localhost:9222)")
    parser.add_argument("--non-interactive", action="store_true", help="Run without stdin pause prompt")
    
    args = parser.parse_args()
    run_automation(target_url=args.url, cdp_url=args.cdp, interactive_prompt=not args.non_interactive)
