from app import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        UPDATE customer_communications 
        SET is_read = TRUE, status = 'READ' 
        WHERE direction = 'INBOUND' AND (is_read = FALSE OR is_read IS NULL);
    """)
    updated = cur.rowcount
    conn.commit()
    print(f"Successfully marked {updated} unread communication(s) as READ.")
conn.close()
