import os

app_path = r"d:\VRTServices\app.py"
dashboard_path = r"d:\VRTServices\templates\dashboard.html"

# 1. Update app.py reopen_customer_checklist to sync compliance event back to Pending
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_reopen_backend = '''            # Reopen step: uncheck last step so accountant can correct mistake
            cur.execute("""
                UPDATE customer_task_checklist
                SET accountant_reviewed = FALSE, tax_accepted = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s AND period = %s;
            """, (real_cust_id, period))
            conn.commit()'''

new_reopen_backend = '''            # Reopen step: uncheck last step so accountant can correct mistake
            cur.execute("""
                UPDATE customer_task_checklist
                SET accountant_reviewed = FALSE, tax_accepted = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s AND period = %s;
            """, (real_cust_id, period))

            # Sync compliance event back to Pending
            try:
                ym_str = period[:7] if (period and len(period) >= 7 and "-" in period[:7]) else None
                if ym_str:
                    cur.execute("""
                        UPDATE compliance_calendar_events
                        SET status = 'Pending', updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s AND category = 'Bookkeeping Close' AND due_date LIKE %s;
                    """, (real_cust_id, f"{ym_str}%"))
                else:
                    cur.execute("""
                        UPDATE compliance_calendar_events
                        SET status = 'Pending', updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s AND category = 'Bookkeeping Close';
                    """, (real_cust_id,))
            except Exception as comp_sync_err:
                print(f"Warning: Failed to sync compliance on period reopen: {comp_sync_err}")

            conn.commit()'''

if old_reopen_backend in app_content:
    app_content = app_content.replace(old_reopen_backend, new_reopen_backend)
    print("Updated app.py reopen_customer_checklist backend logic successfully!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. Update templates/dashboard.html reopenChecklistPeriod and button HTML
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_content = f.read()

old_reopen_btn = '''<button id="btnReopenChecklist" onclick="reopenChecklistPeriod()" style="display: none; padding: 5px 12px; background: rgba(250,204,21,0.15); border: 1px solid rgba(250,204,21,0.4); color: #facc15; border-radius: 8px; font-size: 0.76rem; font-weight: 700; cursor: pointer; transition: all 0.2s;" title="Re-open this period as In Process to make corrections">↩️ Re-open Period</button>'''

new_reopen_btn = '''<button type="button" id="btnReopenChecklist" onclick="reopenChecklistPeriod(event)" style="display: none; padding: 5px 12px; background: rgba(250,204,21,0.15); border: 1px solid rgba(250,204,21,0.4); color: #facc15; border-radius: 8px; font-size: 0.76rem; font-weight: 700; cursor: pointer; transition: all 0.2s;" title="Re-open this period as In Process to make corrections">↩️ Re-open Period</button>'''

if old_reopen_btn in dash_content:
    dash_content = dash_content.replace(old_reopen_btn, new_reopen_btn)
    print("Updated btnReopenChecklist HTML in dashboard.html successfully!")

old_reopen_js = '''        async function reopenChecklistPeriod() {
            if (!currentChecklistCustomerId || !currentChecklistPeriod) return;
            if (!await showCustomConfirm('Re-open this period as In Process to make corrections?')) return;
            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/reopen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ period: currentChecklistPeriod, workflow_mode: activeWorkflowTab })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to reopen period');

                alert('↩️ Period re-opened as In Process!');
                await loadCustomerChecklist(currentChecklistCustomerId, currentChecklistPeriod);
            } catch (err) {
                alert(`❌ Reopen Error: ${err.message}`);
            }
        }'''

new_reopen_js = '''        async function reopenChecklistPeriod(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            if (!currentChecklistCustomerId || !currentChecklistPeriod) return;

            let confirmed = false;
            if (typeof showCustomConfirm === 'function') {
                confirmed = await showCustomConfirm('Re-open this period as In Process to make corrections?', 'Re-open Period', 'Yes, Re-open', 'Cancel');
            } else {
                confirmed = confirm('Re-open this period as In Process to make corrections?');
            }
            if (!confirmed) return;

            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/reopen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ period: currentChecklistPeriod, workflow_mode: activeWorkflowTab })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to reopen period');

                if (typeof showAlert === 'function') showAlert('↩️ Period re-opened as In Process!', 'success', 'Period Re-opened');
                else alert('↩️ Period re-opened as In Process!');

                await loadCustomerChecklist(currentChecklistCustomerId, currentChecklistPeriod);
                if (typeof loadComplianceData === 'function') await loadComplianceData();
            } catch (err) {
                alert(`❌ Reopen Error: ${err.message}`);
            }
        }'''

if old_reopen_js in dash_content:
    dash_content = dash_content.replace(old_reopen_js, new_reopen_js)
    print("Updated reopenChecklistPeriod JS in dashboard.html successfully!")

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

print("Finished applying reopen period fix.")
