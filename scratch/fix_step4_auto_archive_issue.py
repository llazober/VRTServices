import os

app_path = r"d:\VRTServices\app.py"
dashboard_path = r"d:\VRTServices\templates\dashboard.html"

# 1. Update app.py toggle_customer_checklist_step to return the current period's updated checklist
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_return_block = '''        # If period just completed and shifted to next month, fetch the new In Process checklist
        if val and old_in_process_slug != new_in_process_slug:
            res = await get_customer_checklist(real_cust_id, new_in_process_slug, workflow_mode, request)
            res["just_archived"] = True
            res["archived_message"] = f"🎉 {old_in_process_label} Completed & Archived! In Process reset for {new_in_process_label}"
            return res
        else:
            return await get_customer_checklist(real_cust_id, period, workflow_mode, request)'''

new_return_block = '''        # Always return updated checklist for current period so UI shows Step 4 checked (100% complete)
        return await get_customer_checklist(real_cust_id, period, workflow_mode, request)'''

if old_return_block in app_content:
    app_content = app_content.replace(old_return_block, new_return_block)
    print("Updated app.py toggle return block successfully!")

# Ensure 2-way sync updates all active & target periods
old_sync_block = '''                in_proc_slug, _ = get_in_process_period(cur, cid, "bookkeeping")
                periods_to_update = list(set([p for p in [ym_slug, in_proc_slug] if p]))'''

new_sync_block = '''                in_proc_slug, _ = get_in_process_period(cur, cid, "bookkeeping")
                periods_to_update = list(set([p for p in [ym_slug, in_proc_slug, "in_process"] if p]))'''

if old_sync_block in app_content:
    app_content = app_content.replace(old_sync_block, new_sync_block)
    print("Updated 2-way sync periods in app.py successfully!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. Update templates/dashboard.html to stop propagation on checkbox click
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_content = f.read()

old_chk_html = '''<input type="checkbox" id="step_accountant_reviewed" onchange="toggleChecklistStep('accountant_reviewed', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">'''
new_chk_html = '''<input type="checkbox" id="step_accountant_reviewed" onchange="toggleChecklistStep('accountant_reviewed', this.checked)" onclick="event.stopPropagation()" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">'''

if old_chk_html in dash_content:
    dash_content = dash_content.replace(old_chk_html, new_chk_html)
    print("Added stopPropagation to Step 4 checkbox in dashboard.html!")

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

print("Finished applying Step 4 fix.")
