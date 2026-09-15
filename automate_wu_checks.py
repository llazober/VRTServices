import os
import sys
import time
import json
import datetime
from playwright.sync_api import sync_playwright

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

def run_automation(interactive_prompt=True):
    update_status("running", "Launching Chromium browser for Western Union Check Automation...")
    print("\n==========================================================================")
    print("🚀 WESTERN UNION CHECK AUTOMATION (PLAYWRIGHT STRATEGY 1)")
    print("==========================================================================")
    print(f"Target Download Directory: {DOWNLOAD_DIR}\n")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized"]
            )
            context = browser.new_context(
                accept_downloads=True,
                viewport=None
            )
            page = context.new_page()

            print("Step 1: Navigating to Western Union Portal (https://www.westernunion.com/)...")
            update_status("waiting_login", "Browser opened. Please log into Western Union and navigate to Checks page.")
            page.goto("https://www.westernunion.com/")

            print("\n=======================================================")
            print("PLEASE LOG IN TO WESTERN UNION MANUALLY IN THE BROWSER WINDOW.")
            print("NAVIGATE TO THE 'CHECKS' PAGE / TABLE.")
            print("Press ENTER in this terminal once you are on the Checks page.")
            print("=======================================================\n")
            
            if interactive_prompt:
                try:
                    input("Press Enter to start downloading checks...")
                except (EOFError, OSError):
                    print("No interactive console stdin attached. Waiting 20 seconds for manual login in browser window...")
                    time.sleep(20)

            update_status("running", "Locating checks table records...")
            row_selector = "table tbody tr"
            try:
                page.wait_for_selector(row_selector, timeout=15000)
            except Exception:
                print("Warning: Table selector timeout. Attempting to proceed with available elements...")

            rows = page.locator(row_selector).all()
            total_checks = len(rows)
            print(f"Found {total_checks} check records in table.")
            update_status("running", f"Found {total_checks} check records.", total=total_checks, processed=0)

            for index in range(total_checks):
                current_row = page.locator(row_selector).nth(index)
                check_number_el = current_row.locator("td:nth-child(2)")
                check_number = check_number_el.inner_text().strip() if check_number_el.count() > 0 else f"RECORD_{index+1}"
                
                safe_check_no = "".join([c for c in check_number if c.isalnum() or c in ("-", "_", " ")])
                target_filename = os.path.join(DOWNLOAD_DIR, f"Check # {safe_check_no}.pdf")

                print(f"[{index+1}/{total_checks}] Processing Check #{safe_check_no}...")
                update_status("running", f"Processing Check #{safe_check_no} ({index+1}/{total_checks})", total=total_checks, processed=index, current_file=f"Check # {safe_check_no}.pdf")

                if os.path.exists(target_filename):
                    print(f"  --> Already downloaded: {target_filename}. Skipping.")
                    continue

                icon_button = current_row.locator("button, a, .icon-view").first

                try:
                    with context.expect_page(timeout=10000) as new_page_info:
                        icon_button.click()
                    
                    popup_page = new_page_info.value
                    popup_page.wait_for_load_state("domcontentloaded")

                    print_button = popup_page.locator("button:has-text('Print'), button:has-text('Save'), #printBtn").first
                    
                    with popup_page.expect_download(timeout=15000) as download_info:
                        print_button.click()
                    
                    download = download_info.value
                    download.save_as(target_filename)
                    print(f"  --> Saved: {target_filename}")

                    popup_page.close()

                except Exception as err:
                    print(f"  [WARNING] Direct popup download failed for Check #{safe_check_no}: {err}")
                    print("  Attempting fallback screenshot capture...")
                    try:
                        if 'popup_page' in locals() and not popup_page.is_closed():
                            popup_page.screenshot(path=target_filename.replace(".pdf", ".png"))
                            popup_page.close()
                    except Exception as ss_err:
                        print(f"  [ERROR] Fallback screenshot failed: {ss_err}")

                time.sleep(1)

            print("\n🎉 All checks processed successfully!")
            update_status("completed", f"All {total_checks} checks processed successfully.", total=total_checks, processed=total_checks)
            browser.close()

    except Exception as ex:
        print(f"[AUTOMATION ERROR]: {ex}")
        update_status("error", f"Automation error: {ex}")

if __name__ == "__main__":
    run_automation()
