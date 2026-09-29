#!/usr/bin/env python3
import os
import sys
import time
import datetime
import subprocess
import zoneinfo
import boto3
from dotenv import load_dotenv

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
DB_NAME = os.environ.get("POSTGRES_DB") or "VRT"
DB_URL = os.environ.get("DATABASE_URL")
DO_KEY = os.environ.get("DO_SPACES_KEY")
DO_SECRET = os.environ.get("DO_SPACES_SECRET")
DO_ENDPOINT = os.environ.get("DO_SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
DO_BUCKET = os.environ.get("DO_SPACES_BUCKET", "datalazocrm")
DO_REGION = os.environ.get("DO_SPACES_REGION", "nyc3")

LOCAL_BACKUP_DIR = "/var/backups/vrt_postgres"
BACKUP_FILENAME = f"vrt_db_backup_{TIMESTAMP_STR}.sql.gz"
LOCAL_FILE_PATH = os.path.join(LOCAL_BACKUP_DIR, BACKUP_FILENAME)
REMOTE_KEY = f"db_backups/{BACKUP_FILENAME}"

def run_db_backup():
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🚀 Starting PostgreSQL Database Backup...")
    
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
        pg_dump_path = "pg_dump"

    # Dump & compress database using pg_dump
    pg_dump_cmd = f"pg_dump '{DB_URL}' | gzip > '{LOCAL_FILE_PATH}'"
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 📦 Dumping & compressing database to {LOCAL_FILE_PATH}...")
    
    res = subprocess.run(pg_dump_cmd, shell=True, capture_output=True, text=True)
    
    file_size_bytes = os.path.getsize(LOCAL_FILE_PATH) if os.path.exists(LOCAL_FILE_PATH) else 0
    file_size_mb = file_size_bytes / (1024 * 1024)

    if res.returncode != 0 or file_size_bytes < 100:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ pg_dump failed or produced empty backup ({file_size_bytes} bytes). Stdout/Stderr: {res.stderr}")
        sys.exit(1)
        
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ✅ Local backup created successfully ({file_size_mb:.2f} MB)")

    # Upload offsite to DigitalOcean Spaces bucket (datalazocrm)
    if not DO_KEY or not DO_SECRET:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ DO_SPACES_KEY or DO_SPACES_SECRET missing. Skipping offsite upload.")
        return

    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ☁️ Uploading to DigitalOcean Space '{DO_BUCKET}' at '{REMOTE_KEY}'...")
    try:
        session = boto3.session.Session()
        s3 = session.client(
            's3',
            region_name=DO_REGION,
            endpoint_url=DO_ENDPOINT,
            aws_access_key_id=DO_KEY,
            aws_secret_access_key=DO_SECRET
        )
        s3.upload_file(LOCAL_FILE_PATH, DO_BUCKET, REMOTE_KEY)
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🌐 Offsite upload to DigitalOcean Spaces completed successfully!")
    except Exception as e:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ Failed to upload to DigitalOcean Spaces: {e}")

    # Prune local backups older than 7 days
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🧹 Cleaning up local backups older than 7 days...")
    cutoff_time = time.time() - (7 * 86400)
    for fname in os.listdir(LOCAL_BACKUP_DIR):
        fpath = os.path.join(LOCAL_BACKUP_DIR, fname)
        if os.path.isfile(fpath) and fname.startswith("vrt_db_backup_") and os.path.getmtime(fpath) < cutoff_time:
            os.remove(fpath)
            print(f"   Deleted old local backup: {fname}")

    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🎉 Database Backup Completed Successfully.")

if __name__ == "__main__":
    run_db_backup()
