import os

app_path = r"d:\VRTServices\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old_reopen_func = '''@app.post("/api/customers/{customer_id}/checklist/reopen")
async def reopen_customer_checklist(customer_id: str, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    period = (data.get("period") or "").strip()
    workflow_mode = data.get("workflow_mode") or "bookkeeping"
    if not period:
        raise HTTPException(status_code=400, detail="Period is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cid_str = str(customer_id).strip()
            if cid_str.isdigit():
                cur.execute("SELECT id FROM customer WHERE id = %s OR custumer_number = %s;", (int(cid_str), cid_str))
            else:
                cur.execute("SELECT id FROM customer WHERE custumer_number = %s OR display_name = %s OR legal_name = %s;", (cid_str, cid_str, cid_str))
            cust_row = cur.fetchone()
            real_cust_id = cust_row["id"] if cust_row else (int(cid_str) if cid_str.isdigit() else 0)

            # Reopen step: uncheck last step so accountant can correct mistake
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

            conn.commit()

        return await get_customer_checklist(customer_id=real_cust_id, period=period, workflow_tab=workflow_mode, request=request)
    except Exception as e:
        print(f"Error reopening customer checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()'''

new_reopen_func = '''@app.post("/api/customers/{customer_id}/checklist/reopen")
async def reopen_customer_checklist(customer_id: str, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    period = (data.get("period") or "").strip()
    workflow_mode = data.get("workflow_mode") or "bookkeeping"
    if not period:
        raise HTTPException(status_code=400, detail="Period is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cid_str = str(customer_id).strip()
            cust = None
            if cid_str.isdigit():
                cur.execute("SELECT * FROM customer WHERE id = %s OR custumer_number = %s;", (int(cid_str), cid_str))
                cust = cur.fetchone()
            if not cust:
                cur.execute("SELECT * FROM customer WHERE custumer_number = %s OR display_name = %s OR legal_name = %s;", (cid_str, cid_str, cid_str))
                cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

            real_cust_id = cust["id"]
            in_process_slug, in_process_label = get_in_process_period(cur, real_cust_id, workflow_mode)
            target_period = in_process_slug if (not period or period == "in_process") else period

            # Reopen step: uncheck last step so accountant can correct mistake
            cur.execute("""
                UPDATE customer_task_checklist
                SET accountant_reviewed = FALSE, tax_accepted = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s AND (period = %s OR period = %s);
            """, (real_cust_id, target_period, period))

            # Sync compliance event back to Pending
            try:
                ym_str = target_period[:7] if (target_period and len(target_period) >= 7 and "-" in target_period[:7]) else None
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

            conn.commit()

        return await get_customer_checklist(customer_id=str(real_cust_id), period=target_period, workflow_tab=workflow_mode, request=request)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error reopening customer checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()'''

if old_reopen_func in content:
    content = content.replace(old_reopen_func, new_reopen_func)
    print("Replaced reopen_customer_checklist function in app.py successfully!")
else:
    print("WARNING: Old reopen_customer_checklist function target not found exact match!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Customer lookup reopen fix complete.")
