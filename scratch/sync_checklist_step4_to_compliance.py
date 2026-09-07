import os

app_path = r"d:\VRTServices\app.py"
dashboard_path = r"d:\VRTServices\templates\dashboard.html"

# 1. Update app.py toggle_customer_checklist_step
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_step_update = '''            if step_key and step_key in col_map:
                col_name = col_map[step_key]
                cur.execute(f"""
                    UPDATE customer_task_checklist
                    SET {col_name} = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND period = %s;
                """, (val, real_cust_id, period))'''

new_step_update = '''            if step_key and step_key in col_map:
                col_name = col_map[step_key]
                cur.execute(f"""
                    UPDATE customer_task_checklist
                    SET {col_name} = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND period = %s;
                """, (val, real_cust_id, period))

                # ── AUTOMATIC SYNC WITH COMPLIANCE CALENDAR MODULE ─────────────────
                try:
                    if step_key == "accountant_reviewed":
                        new_status = "Completed" if val else "Pending"
                        ym_str = None
                        if period and len(period) >= 7 and "-" in period[:7]:
                            ym_str = period[:7]

                        # 1. Try matching year-month for Bookkeeping Close
                        if ym_str:
                            cur.execute("""
                                UPDATE compliance_calendar_events
                                SET status = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE customer_id = %s AND category = 'Bookkeeping Close' AND due_date LIKE %s;
                            """, (new_status, real_cust_id, f"{ym_str}%"))

                        # 2. Try matching any pending Bookkeeping Close event for customer
                        if cur.rowcount == 0:
                            cur.execute("""
                                UPDATE compliance_calendar_events
                                SET status = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id IN (
                                    SELECT id FROM compliance_calendar_events
                                    WHERE customer_id = %s AND category = 'Bookkeeping Close'
                                    ORDER BY due_date ASC
                                    LIMIT 1
                                );
                            """, (new_status, real_cust_id))

                        # 3. If no event existed at all, auto-create the Bookkeeping Close compliance deadline
                        if cur.rowcount == 0:
                            import datetime
                            due_date_str = f"{ym_str}-15" if (ym_str and len(ym_str)==7) else datetime.date.today().isoformat()
                            tax_prep = cust.get("assigned_user_id") or None
                            title_period = period.replace("_", " ").title() if period else "Monthly"
                            cur.execute("""
                                INSERT INTO compliance_calendar_events (
                                    customer_id, category, title, description, jurisdiction,
                                    due_date, frequency, assigned_tax_prep, status
                                ) VALUES (
                                    %s, 'Bookkeeping Close', %s, 'Monthly Bookkeeping Close & Reconciliations', 'Internal',
                                    %s, 'Monthly', %s, %s
                                );
                            """, (
                                real_cust_id, f"Monthly Bookkeeping Close - {title_period}",
                                due_date_str, tax_prep, new_status
                            ))

                    elif step_key in ("tax_efile", "tax_accepted"):
                        new_status = "Completed" if val else "Pending"
                        cur.execute("""
                            UPDATE compliance_calendar_events
                            SET status = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE customer_id = %s AND category IN ('Corporate Tax', 'Estimated Tax', '1099/W2');
                        """, (new_status, real_cust_id))
                except Exception as sync_comp_err:
                    print(f"Warning: Auto-syncing checklist step to compliance failed: {sync_comp_err}")'''

if old_step_update in app_content:
    app_content = app_content.replace(old_step_update, new_step_update)
    print("Updated app.py toggle_customer_checklist_step successfully!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. Update templates/dashboard.html toggleChecklistStep
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_content = f.read()

old_toggle_js = '''                if (typeof fetchPendingWorkload === 'function') {
                    fetchPendingWorkload();
                }'''

new_toggle_js = '''                if (typeof fetchPendingWorkload === 'function') {
                    fetchPendingWorkload();
                }
                if (typeof loadComplianceData === 'function') {
                    loadComplianceData();
                }'''

if old_toggle_js in dash_content:
    dash_content = dash_content.replace(old_toggle_js, new_toggle_js)
    print("Updated templates/dashboard.html toggleChecklistStep successfully!")

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

print("Step 4 -> Compliance sync patch complete.")
