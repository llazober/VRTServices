import sys
import os
sys.path.insert(0, os.getcwd())

from app import get_db_connection
from psycopg2.extras import RealDictCursor

conn = get_db_connection()
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    print("--- RAW customer_billing_schedules TABLE ---")
    cur.execute("SELECT * FROM customer_billing_schedules;")
    schedules = cur.fetchall()
    print(f"Total schedules in DB: {len(schedules)}")
    for s in schedules:
        print(dict(s))
    
    print("\n--- INNER JOIN QUERY ---")
    cur.execute("""
        SELECT s.*, c.custumer_number, c.legal_name, c.email
        FROM customer_billing_schedules s
        JOIN customer c ON s.customer_id = c.id;
    """)
    inner_rows = cur.fetchall()
    print(f"Inner join returned rows: {len(inner_rows)}")

    print("\n--- LEFT JOIN QUERY ---")
    cur.execute("""
        SELECT s.*, c.custumer_number, c.legal_name, c.email, c.display_name
        FROM customer_billing_schedules s
        LEFT JOIN customer c ON (s.customer_id::text = c.id::text OR s.customer_id::text = c.custumer_number)
    """)
    left_rows = cur.fetchall()
    print(f"Left join returned rows: {len(left_rows)}")
    for r in left_rows:
        print(dict(r))

conn.close()
