import os

app_path = r"d:\VRTServices\app.py"
dashboard_path = r"d:\VRTServices\templates\dashboard.html"

# 1. Update app.py update_compliance_event_status
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_status_route = '''            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Compliance event not found.")
            
            conn.commit()
            res = dict(row)'''

new_status_route = '''            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Compliance event not found.")

            # ── 2-WAY SYNC TO WORKFLOW CHECKLIST ─────────────────────────────
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
                print(f"Warning: Failed to sync compliance event status to checklist: {sync_err}")
            
            conn.commit()
            res = dict(row)'''

if old_status_route in app_content:
    app_content = app_content.replace(old_status_route, new_status_route)
    print("Updated app.py update_compliance_event_status successfully!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. Update templates/dashboard.html toggleComplianceStatus and make checklist cards clickable
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_content = f.read()

old_toggle_comp = '''        async function toggleComplianceStatus(event, id, newStatus) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                const res = await fetch(`/api/compliance/events/${id}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    await loadComplianceData();
                }
            } catch (err) {
                alert('Error updating status: ' + err.message);
            }
        }'''

new_toggle_comp = '''        async function toggleComplianceStatus(event, id, newStatus) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                const res = await fetch(`/api/compliance/events/${id}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    await loadComplianceData();
                    if (typeof currentChecklistCustomerId !== 'undefined' && currentChecklistCustomerId) {
                        await loadCustomerChecklist(currentChecklistCustomerId, currentChecklistPeriod);
                    }
                }
            } catch (err) {
                alert('Error updating status: ' + err.message);
            }
        }'''

if old_toggle_comp in dash_content:
    dash_content = dash_content.replace(old_toggle_comp, new_toggle_comp)
    print("Updated toggleComplianceStatus in dashboard.html successfully!")

# Make step_accountant_reviewed_card and other checklist cards clickable across the entire row
old_card_html = '''                <!-- Step 4 -->
                <div id="step_accountant_reviewed_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">'''

new_card_html = '''                <!-- Step 4 -->
                <div id="step_accountant_reviewed_card" onclick="if(event.target.tagName !== 'INPUT') { const c = document.getElementById('step_accountant_reviewed'); c.checked = !c.checked; toggleChecklistStep('accountant_reviewed', c.checked); }" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s; cursor: pointer;">'''

if old_card_html in dash_content:
    dash_content = dash_content.replace(old_card_html, new_card_html)
    print("Made step_accountant_reviewed_card clickable successfully!")

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

print("2-way compliance <-> checklist sync patch complete.")
