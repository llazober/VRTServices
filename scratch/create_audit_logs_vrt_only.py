import os
import urllib.parse
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

db_url = os.environ.get("DATABASE_URL") or "postgresql://postgres:Paris2025%24@161.35.119.223:5432/VRT?sslmode=disable"
parsed = urllib.parse.urlparse(db_url)
vrt_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/VRT", parsed.params, parsed.query, parsed.fragment))

print(f"Connecting to VRT DB: {vrt_url}")

try:
    conn = psycopg2.connect(vrt_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(150) NOT NULL,
                ip_address VARCHAR(64) DEFAULT 'Unknown',
                tenant_name VARCHAR(100) DEFAULT 'VRT Services',
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(100) NOT NULL,
                entity_id VARCHAR(255) DEFAULT NULL,
                details JSONB DEFAULT '{}'::jsonb,
                status VARCHAR(50) DEFAULT 'SUCCESS'
            );

            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_username ON audit_logs (username);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
        """)
    print("SUCCESS: Created audit_logs table & indexes in VRT database.")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
