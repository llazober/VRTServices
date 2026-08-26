from app import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        SELECT id, customer_id, subject, direction, is_read, status, created_at 
        FROM customer_communications 
        WHERE direction = 'INBOUND';
    """)
    rows = cur.fetchall()
    print("=== INBOUND COMMUNICATIONS ===")
    for r in rows:
        print(r)

conn.close()
