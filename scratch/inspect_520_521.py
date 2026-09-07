import os, json, sys
sys.path.insert(0, ".")
from app import get_db_connection, RealDictCursor

conn = get_db_connection()
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("SELECT id, status, payload_json, created_at FROM webhook_debug_log WHERE id IN (520, 521);")
    rows = cur.fetchall()
    for r in rows:
        print(f"=== LOG ID {r['id']} (Status: {r['status']}) ===")
        print("Payload:", json.dumps(r['payload_json'], indent=2))
conn.close()
