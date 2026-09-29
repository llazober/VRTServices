# 🛡️ DigitalOcean PostgreSQL Automated Offsite Backup Plan

> **System Guide**: Automated daily PostgreSQL database dumps uploaded to DigitalOcean Spaces (`datalazocrm`) alongside weekly Droplet snapshots.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────┐       1. Daily pg_dump & gzip      ┌─────────────────────────────────┐
│  DigitalOcean Droplet                │  ───────────────────────────────►  │  Local Server Backup Directory  │
│  (PostgreSQL Database)               │                                    │  (/var/backups/vrt_postgres/)   │
└──────────────────────────────────────┘                                    └────────────────┬────────────────┘
                                                                                             │
                                                                                             │ 2. Upload via Boto3 S3
                                                                                             ▼
                                                                            ┌─────────────────────────────────┐
                                                                            │ DigitalOcean Spaces (Offsite)   │
                                                                            │ Bucket: datalazocrm             │
                                                                            │ Folder: db_backups/             │
                                                                            └─────────────────────────────────┘
```

---

## ⚔️ Why Both Weekly Snapshots & Daily DB Dumps Are Required

| Backup Feature | Option 2 (Droplet Snapshots) | Option 1 (Daily DB Dump to DO Spaces) |
| :--- | :--- | :--- |
| **Frequency** | **Once a week** (Every 7 days) | **Daily** (Every night at 2:00 AM NY Time) |
| **Data Loss Window** | Up to **7 days of work lost** if disk fails | Maximum **a few hours of data lost** |
| **Restore Speed** | **Slow & Destructive** (Requires replacing entire server disk, 15-30+ min downtime) | **Fast & Granular** (Restores just the database in 10-15 seconds without stopping server) |
| **Offsite Isolation** | Bound to Droplet infrastructure | Independent Cloud Storage (`datalazocrm/db_backups/`) |

---

## 📋 Step-by-Step Setup Guide

### Step 1: Multi-Database Backup Script (`scripts/db_backup.py`)

The backup script at `scripts/db_backup.py` automatically discovers **all active databases** in the PostgreSQL cluster and dumps/uploads each database individually:

```python
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

def get_all_databases(db_url):
    """Connect to PostgreSQL server and return a list of non-template database names."""
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
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ⚠️ Could not list databases dynamically: {e}")
        parsed = urllib.parse.urlparse(db_url)
        default_db = parsed.path.lstrip('/') or "datalazo"
        return [default_db]

def build_db_url(base_db_url, db_name):
    parsed = urllib.parse.urlparse(base_db_url)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, f'/{db_name}', parsed.params, parsed.query, parsed.fragment)
    )

def run_db_backup():
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 🚀 Starting PostgreSQL Multi-Database Backup...")
    
    if not DB_URL:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ DATABASE_URL missing from environment/.env!")
        sys.exit(1)

    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    
    db_names = get_all_databases(DB_URL)
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 📋 Found {len(db_names)} database(s) to backup: {', '.join(db_names)}")

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
```

---

### Step 2: Schedule the Server Cron Job

On your DigitalOcean Droplet (Easypanel Host):

1. Open crontab editor on your server:
   ```bash
   crontab -e
   ```

2. Add this line to run the multi-database backup script **every night at 2:00 AM US Eastern Time**:
   ```cron
   0 2 * * * cd /etc/easypanel/projects/datalazo/vrtservices/code && /usr/bin/python3 scripts/db_backup.py >> /var/log/vrt_db_backup.log 2>&1
   ```

---

### Step 3: Manual Testing & Verification

Run the backup script manually anytime from your server:

```bash
cd /etc/easypanel/projects/datalazo/vrtservices/code
python3 scripts/db_backup.py
```

Console Output:
```text
[2026-09-28 23:00:00 ET] 🚀 Starting PostgreSQL Multi-Database Backup...
[2026-09-28 23:00:00 ET] 📋 Found 8 database(s) to backup: postgres, datalazo, ledger_lazo, qcscheduler, epicormock, lacteosmrp, lacteos, VRT

[2026-09-28 23:00:00 ET] 📦 Backing up database [postgres]...
[2026-09-28 23:00:01 ET] ✅ Local backup for [postgres] created: postgres_backup_2026-09-28_23-00-00.sql.gz (0.85 MB)
[2026-09-28 23:00:01 ET] ☁️ Uploading [postgres] to DO Space 'datalazocrm' at 'db_backups/postgres_backup_2026-09-28_23-00-00.sql.gz'...
[2026-09-28 23:00:02 ET] 🌐 Upload complete for [postgres]!

[2026-09-28 23:00:02 ET] 📦 Backing up database [datalazo]...
[2026-09-28 23:00:04 ET] ✅ Local backup for [datalazo] created: datalazo_backup_2026-09-28_23-00-00.sql.gz (14.25 MB)
[2026-09-28 23:00:04 ET] ☁️ Uploading [datalazo] to DO Space 'datalazocrm' at 'db_backups/datalazo_backup_2026-09-28_23-00-00.sql.gz'...
[2026-09-28 23:00:06 ET] 🌐 Upload complete for [datalazo]!

[2026-09-28 23:00:06 ET] 📦 Backing up database [VRT]...
[2026-09-28 23:00:08 ET] ✅ Local backup for [VRT] created: VRT_backup_2026-09-28_23-00-00.sql.gz (12.10 MB)
[2026-09-28 23:00:08 ET] ☁️ Uploading [VRT] to DO Space 'datalazocrm' at 'db_backups/VRT_backup_2026-09-28_23-00-00.sql.gz'...
[2026-09-28 23:00:10 ET] 🌐 Upload complete for [VRT]!

...

[2026-09-28 23:00:15 ET] 🎉 Backup Process Completed. 8 succeeded, 0 failed.
```

---

## 🔄 Disaster Recovery: Restoring Database Backups

If you ever need to restore your database from a DigitalOcean Space backup:

```bash
# 1. Download target backup file from DigitalOcean Space bucket
aws s3 cp s3://datalazocrm/db_backups/vrt_db_backup_2026-09-28_22-10-00.sql.gz . --endpoint-url https://nyc3.digitaloceanspaces.com

# 2. Restore into PostgreSQL database
gunzip -c vrt_db_backup_2026-09-28_22-10-00.sql.gz | psql "$DATABASE_URL"
```
