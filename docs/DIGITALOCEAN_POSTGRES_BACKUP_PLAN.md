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

### Step 1: Create the Backup Script (`scripts/db_backup.py`)

Create a script file in your project directory at `scripts/db_backup.py`:

```python
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
    
    # 1. Ensure local backup directory exists
    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    
    # 2. Dump & compress database using pg_dump
    pg_dump_cmd = f"pg_dump '{DB_URL}' | gzip > '{LOCAL_FILE_PATH}'"
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] 📦 Dumping & compressing database to {LOCAL_FILE_PATH}...")
    
    res = subprocess.run(pg_dump_cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ❌ pg_dump failed: {res.stderr}")
        sys.exit(1)
        
    file_size_mb = os.path.getsize(LOCAL_FILE_PATH) / (1024 * 1024)
    print(f"[{NOW_ET.strftime('%Y-%m-%d %H:%M:%S')} ET] ✅ Local backup created successfully ({file_size_mb:.2f} MB)")

    # 3. Upload offsite to DigitalOcean Spaces bucket (datalazocrm)
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

    # 4. Prune local backups older than 7 days
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
```

---

### Step 2: Schedule the Server Cron Job

On your DigitalOcean Droplet:

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line to run the backup script **every night at 2:00 AM US Eastern Time**:
   ```cron
   0 2 * * * cd /var/www/VRTServices && /usr/bin/python3 scripts/db_backup.py >> /var/log/vrt_db_backup.log 2>&1
   ```

---

### Step 3: Manual Testing & Verification

Run the backup script manually anytime to verify:

```bash
cd /var/www/VRTServices
python3 scripts/db_backup.py
```

Console Output:
```text
[2026-09-28 22:10:00 ET] 🚀 Starting PostgreSQL Database Backup...
[2026-09-28 22:10:00 ET] 📦 Dumping & compressing database to /var/backups/vrt_postgres/vrt_db_backup_2026-09-28_22-10-00.sql.gz...
[2026-09-28 22:10:02 ET] ✅ Local backup created successfully (14.25 MB)
[2026-09-28 22:10:02 ET] ☁️ Uploading to DigitalOcean Space 'datalazocrm' at 'db_backups/vrt_db_backup_2026-09-28_22-10-00.sql.gz'...
[2026-09-28 22:10:05 ET] 🌐 Offsite upload to DigitalOcean Spaces completed successfully!
[2026-09-28 22:10:05 ET] 🎉 Database Backup Completed Successfully.
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
