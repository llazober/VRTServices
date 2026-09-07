import os

app_path = r"d:\VRTServices\app.py"
dashboard_path = r"d:\VRTServices\templates\dashboard.html"

# 1. Update app.py update_compliance_event_status
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_status_sync = '''            # ── 2-WAY SYNC TO WORKFLOW CHECKLIST ─────────────────────────────
            try:
                cid = row["customer_id"]
                cat = (row.get("category") or "").strip()
                is_done = (new_status == "Completed")
                due_d = row.get("due_date")

                ym_slug = None
                if due_d:
                    try:
                        import datetime
                        d_obj = due_d if hasattr(due_d, 'strftime') else datetime.date.fromisoformat(str(due_d)[:10])
                        ym_slug = d_obj.strftime("%Y-%m")
                    except Exception:
                        pass

                cur.execute("SELECT period FROM customer_task_checklist WHERE customer_id = %s ORDER BY updated_at DESC LIMIT 1;", (cid,))
                chk_row = cur.fetchone()
                target_period = ym_slug if ym_slug else (chk_row["period"] if chk_row else "in_process")

                if cat == "Bookkeeping Close":
                    cur.execute("""
                        INSERT INTO customer_task_checklist (customer_id, period, accountant_reviewed)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (customer_id, period)
                        DO UPDATE SET accountant_reviewed = EXCLUDED.accountant_reviewed, updated_at = CURRENT_TIMESTAMP;
                    """, (cid, target_period, is_done))
                elif cat in ("Corporate Tax", "Estimated Tax", "1099/W2"):
                    cur.execute("""
                        INSERT INTO customer_task_checklist (customer_id, period, tax_efile, tax_accepted)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (customer_id, period)
                        DO UPDATE SET tax_efile = EXCLUDED.tax_efile, tax_accepted = EXCLUDED.tax_accepted, updated_at = CURRENT_TIMESTAMP;
                    """, (cid, target_period, is_done, is_done))
            except Exception as sync_err:
                print(f"Warning: Failed to sync compliance event status to checklist: {sync_err}")'''

new_status_sync = '''            # ── 2-WAY SYNC TO WORKFLOW CHECKLIST ─────────────────────────────
            try:
                cid = row["customer_id"]
                cat = (row.get("category") or "").strip()
                is_done = (new_status == "Completed")
                due_d = row.get("due_date")

                ym_slug = None
                if due_d:
                    try:
                        import datetime
                        d_obj = due_d if hasattr(due_d, 'strftime') else datetime.date.fromisoformat(str(due_d)[:10])
                        ym_slug = d_obj.strftime("%Y-%m")
                    except Exception:
                        pass

                in_proc_slug, _ = get_in_process_period(cur, cid, "bookkeeping")
                periods_to_update = list(set([p for p in [ym_slug, in_proc_slug] if p]))

                if cat == "Bookkeeping Close":
                    for p_slug in periods_to_update:
                        cur.execute("""
                            INSERT INTO customer_task_checklist (customer_id, period, accountant_reviewed)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (customer_id, period)
                            DO UPDATE SET accountant_reviewed = EXCLUDED.accountant_reviewed, updated_at = CURRENT_TIMESTAMP;
                        """, (cid, p_slug, is_done))
                elif cat in ("Corporate Tax", "Estimated Tax", "1099/W2"):
                    for p_slug in periods_to_update:
                        cur.execute("""
                            INSERT INTO customer_task_checklist (customer_id, period, tax_efile, tax_accepted)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (customer_id, period)
                            DO UPDATE SET tax_efile = EXCLUDED.tax_efile, tax_accepted = EXCLUDED.tax_accepted, updated_at = CURRENT_TIMESTAMP;
                        """, (cid, p_slug, is_done, is_done))
            except Exception as sync_err:
                print(f"Warning: Failed to sync compliance event status to checklist: {sync_err}")'''

if old_status_sync in app_content:
    app_content = app_content.replace(old_status_sync, new_status_sync)
    print("Updated app.py update_compliance_event_status successfully!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. Update templates/dashboard.html toggleChecklistStep
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_content = f.read()

old_toggle_func = '''        async function toggleChecklistStep(stepKey, isChecked) {
            if (!currentChecklistCustomerId || !currentChecklistPeriod) return;
            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        period: currentChecklistPeriod,
                        step_key: stepKey,
                        value: isChecked,
                        workflow_mode: activeWorkflowTab
                    })
                });'''

new_toggle_func = '''        async function toggleChecklistStep(stepKey, isChecked) {
            if (!currentChecklistCustomerId) return;
            const periodToUse = currentChecklistPeriod || document.getElementById('checklistPeriodSelect')?.value || 'in_process';
            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        period: periodToUse,
                        step_key: stepKey,
                        value: isChecked,
                        workflow_mode: activeWorkflowTab
                    })
                });'''

if old_toggle_func in dash_content:
    dash_content = dash_content.replace(old_toggle_func, new_toggle_func)
    print("Updated toggleChecklistStep fallback in dashboard.html successfully!")

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

print("Patch complete.")
