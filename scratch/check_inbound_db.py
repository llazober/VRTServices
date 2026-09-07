import os, psycopg2
from psycopg2.extras import RealDictCursor

target_db = os.environ.get("POSTGRES_DB") or "VRT"
db_url = os.environ.get("DATABASE_URL")
if db_url:
    import urllib.parse
    parsed = urllib.parse.urlparse(db_url)
    new_path = f"/{target_db}"
    db_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))

print(f"Connecting to database: {db_url}")
conn = psycopg2.connect(db_url)
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    print("\n--- LAST 5 WEBHOOK DEBUG LOGS ---")
    try:
        cur.execute("SELECT id, sender_email, recipient_email, subject, status, created_at FROM webhook_debug_log ORDER BY id DESC LIMIT 5;")
        for r in cur.fetchall():
            print(dict(r))
    except Exception as e:
        print(f"Error querying webhook_debug_log: {e}")

    print("\n--- LAST 5 CUSTOMER COMMUNICATIONS (INBOUND) ---")
    try:
        cur.execute("SELECT id, customer_id, sender_email, recipient_email, subject, is_read, created_at FROM customer_communications WHERE direction = 'INBOUND' ORDER BY id DESC LIMIT 5;")
        for r in cur.fetchall():
            print(dict(r))
    except Exception as e:
        print(f"Error querying customer_communications: {e}")

conn.close()
