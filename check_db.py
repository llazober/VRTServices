import os, json, psycopg2
from psycopg2.extras import RealDictCursor

# Load .env if present
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k, v)

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("No DATABASE_URL set in env")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, legal_name, email, parent_name, custumer_number, do_folder_path FROM customer WHERE legal_name ILIKE '%BARCELONA%' OR legal_name ILIKE '%LUIS%';")
        print('=== CUSTOMERS ===')
        print(json.dumps(cur.fetchall(), indent=2, default=str))

        cur.execute("SELECT id, customer_id, sender_email, recipient_email, subject, attachments_json, created_at FROM customer_communications ORDER BY id DESC LIMIT 5;")
        print('=== LAST COMMUNICATIONS ===')
        print(json.dumps(cur.fetchall(), indent=2, default=str))

        cur.execute("SELECT id, created_at, payload_json FROM webhook_debug_log ORDER BY id DESC LIMIT 3;")
        print('=== LAST WEBHOOK LOGS ===')
        print(json.dumps(cur.fetchall(), indent=2, default=str))
except Exception as e:
    print('DB Error:', e)
