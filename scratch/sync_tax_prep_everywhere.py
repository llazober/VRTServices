import os

app_path = r"d:\VRTServices\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update PUT /api/customers/{customer_id} to cascade Tax Prep changes to compliance_calendar_events
old_cust_update = '''            updated_record = cur.fetchone()
            if not updated_record:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Auto-create parent mapping for updated customer'''

new_cust_update = '''            updated_record = cur.fetchone()
            if not updated_record:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Cascade Tax Prep assignment to all compliance calendar events for this customer
            try:
                cur.execute("""
                    UPDATE compliance_calendar_events
                    SET assigned_tax_prep = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s;
                """, (assigned_user_id, real_cust_id))
            except Exception as sync_err:
                print(f"Warning: Failed to sync compliance events on customer update: {sync_err}")

            # Auto-create parent mapping for updated customer'''

if old_cust_update in content:
    content = content.replace(old_cust_update, new_cust_update)
    print("Added Tax Prep cascade to PUT /api/customers/{customer_id}!")

# 2. Update PUT /api/tax-team/{team_id} to cascade Tax Prep name rename across customer & compliance tables
old_team_update = '''@app.put("/api/tax-team/{team_id}")
async def update_tax_team_member(team_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = await request.json()
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tax Prep Name is required")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('UPDATE "TaxTeam" SET "name" = %s, "updatedAt" = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, name;', (name, team_id))
            updated_row = cur.fetchone()
            if not updated_row:
                raise HTTPException(status_code=404, detail="Tax Team member not found")
            conn.commit()
            return dict(updated_row)'''

new_team_update = '''@app.put("/api/tax-team/{team_id}")
async def update_tax_team_member(team_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = await request.json()
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tax Prep Name is required")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT name FROM "TaxTeam" WHERE id = %s;', (team_id,))
            old_row = cur.fetchone()
            old_name = old_row["name"] if old_row else None

            cur.execute('UPDATE "TaxTeam" SET "name" = %s, "updatedAt" = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, name;', (name, team_id))
            updated_row = cur.fetchone()
            if not updated_row:
                raise HTTPException(status_code=404, detail="Tax Team member not found")

            if old_name and old_name != name:
                cur.execute('UPDATE customer SET assigned_user_id = %s WHERE assigned_user_id = %s;', (name, old_name))
                cur.execute('UPDATE compliance_calendar_events SET assigned_tax_prep = %s WHERE assigned_tax_prep = %s;', (name, old_name))

            conn.commit()
            return dict(updated_row)'''

if old_team_update in content:
    content = content.replace(old_team_update, new_team_update)
    print("Added Tax Prep cascade to PUT /api/tax-team/{team_id}!")

# 3. Update PUT /api/compliance/events/{event_id} to sync customer & all events if sync flag passed
old_event_update = '''            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Compliance event not found.")
            conn.commit()'''

new_event_update = '''            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Compliance event not found.")

            if data.get("sync_customer_tax_prep") and data.get("assigned_tax_prep"):
                new_tp = data.get("assigned_tax_prep")
                cid = updated["customer_id"]
                cur.execute("UPDATE customer SET assigned_user_id = %s WHERE id = %s;", (new_tp, cid))
                cur.execute("UPDATE compliance_calendar_events SET assigned_tax_prep = %s WHERE customer_id = %s;", (new_tp, cid))

            conn.commit()'''

if old_event_update in content:
    content = content.replace(old_event_update, new_event_update)
    print("Added Tax Prep sync option to PUT /api/compliance/events/{event_id}!")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Finished updating app.py for Tax Prep synchronization.")
