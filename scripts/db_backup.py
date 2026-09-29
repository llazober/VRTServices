#!/usr/bin/env python3
import os
import sys
import time
import datetime
import subprocess
import zoneinfo
import urllib.parse
import psycopg2
import boto3
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


# Load environment variables from .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# Enforce US Eastern Time (NY)
EASTERN_TZ = zoneinfo.ZoneInfo("America/New_York")
NOW_ET = datetime.datetime.now(EASTERN_TZ)
TIMESTAMP_STR = NOW_ET.strftime("%Y-%m-%d_%H-%M-%S")

# Configuration from .env
DB_URL = os.environ.get("DATABASE_URL")
DO_KEY = os.environ.get("DO_SPACES_KEY")
DO_SECRET = os.environ.get("DO_SPACES_SECRET")
DO_ENDPOINT = os.environ.get("DO_SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
DO_BUCKET = os.environ.get("DO_SPACES_BUCKET", "datalazocrm")
DO_REGION = os.environ.get("DO_SPACES_REGION", "nyc3")

LOCAL_BACKUP_DIR = "/var/backups/vrt_postgres"

# Try importing psycopg2, auto-installing if missing
try:
    import psycopg2
except ImportError:
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ psycopg2 not found. Installing psycopg2-binary...")
    subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], capture_output=True)
    try:
        import psycopg2
    except ImportError:
        psycopg2 = None

def get_all_databases(db_url):
    """Connect to PostgreSQL server and return a list of non-template database names."""
    if psycopg2:
        try:
            parsed = urllib.parse.urlparse(db_url)
            postgres_sys_url = urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, '/postgres', parsed.params, parsed.query, parsed.fragment)
            )
            conn = psycopg2.connect(postgres_sys_url)
            cur = conn.cursor()
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            db_names = [r[0] for r in rows if r[0]]
            if db_names:
                return db_names
        except Exception as e:
            print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ Dynamic database query error: {e}")

    # Fallback: parse base db name from DB_URL and ensure both VRT and datalazo are included
    parsed = urllib.parse.urlparse(db_url)
    default_db = parsed.path.lstrip('/') or "datalazo"
    fallback_set = {default_db, "VRT", "datalazo"}
    return sorted(list(fallback_set))


def build_db_url(base_db_url, db_name):
    """Replace path in base_db_url with target db_name."""
    parsed = urllib.parse.urlparse(base_db_url)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, f'/{db_name}', parsed.params, parsed.query, parsed.fragment)
    )

def run_db_backup():
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🚀 Starting PostgreSQL Multi-Database Backup...")
    
    if not DB_URL:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ DATABASE_URL missing from environment/.env!")
        sys.exit(1)

    # Ensure local backup directory exists
    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    
    # Check if pg_dump is installed on host
    pg_dump_path = subprocess.run("which pg_dump", shell=True, capture_output=True, text=True).stdout.strip()
    if not pg_dump_path:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ pg_dump command not found on host. Installing postgresql-client...")
        subprocess.run("apt-get update && apt-get install -y postgresql-client", shell=True)

    # Discover databases to backup
    db_names = get_all_databases(DB_URL)
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 📋 Found {len(db_names)} database(s) to backup: {', '.join(db_names)}")

    # Initialize S3 / DO Spaces client if keys present
    s3_client = None
    if DO_KEY and DO_SECRET:
        try:
            session = boto3.session.Session()
            s3_client = session.client(
                's3',
                region_name=DO_REGION,
                endpoint_url=DO_ENDPOINT,
                aws_access_key_id=DO_KEY,
                aws_secret_access_key=DO_SECRET
            )
        except Exception as e:
            print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ Failed to initialize DigitalOcean Spaces client: {e}")

    success_count = 0
    fail_count = 0

    for db_name in db_names:
        target_db_url = build_db_url(DB_URL, db_name)
        backup_filename = f"{db_name}_backup_{TIMESTAMP_STR}.sql.gz"
        local_file_path = os.path.join(LOCAL_BACKUP_DIR, backup_filename)
        remote_key = f"db_backups/{backup_filename}"

        print(f"\n[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 📦 Backing up database [{db_name}]...")
        pg_dump_cmd = f"pg_dump '{target_db_url}' | gzip > '{local_file_path}'"
        
        res = subprocess.run(pg_dump_cmd, shell=True, capture_output=True, text=True)
        file_size_bytes = os.path.getsize(local_file_path) if os.path.exists(local_file_path) else 0
        file_size_mb = file_size_bytes / (1024 * 1024)

        if res.returncode != 0 or file_size_bytes < 100:
            print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ pg_dump failed for [{db_name}]. Stdout/Stderr: {res.stderr}")
            fail_count += 1
            continue

        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ✅ Local backup for [{db_name}] created: {backup_filename} ({file_size_mb:.2f} MB)")

        if s3_client:
            print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ☁️ Uploading [{db_name}] to DO Space '{DO_BUCKET}' at '{remote_key}'...")
            try:
                s3_client.upload_file(local_file_path, DO_BUCKET, remote_key)
                print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🌐 Upload complete for [{db_name}]!")
            except Exception as e:
                print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ Failed offsite upload for [{db_name}]: {e}")
        
        success_count += 1

    # Prune local backups older than 7 days
    print(f"\n[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🧹 Cleaning up local backups older than 7 days...")
    cutoff_time = time.time() - (7 * 86400)
    if os.path.exists(LOCAL_BACKUP_DIR):
        for fname in os.listdir(LOCAL_BACKUP_DIR):
            fpath = os.path.join(LOCAL_BACKUP_DIR, fname)
            if os.path.isfile(fpath) and "_backup_" in fname and os.path.getmtime(fpath) < cutoff_time:
                os.remove(fpath)
                print(f"   Deleted old local backup: {fname}")

    print(f"\n[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🎉 Backup Process Completed. {success_count} succeeded, {fail_count} failed.")

if __name__ == "__main__":
    run_db_backup()

