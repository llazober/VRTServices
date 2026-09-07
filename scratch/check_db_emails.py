import sqlite3
import os

db_path = "VRT.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print("Tables in VRT.db:", tables)
    for table in tables:
        try:
            columns = [c[1] for c in cur.execute(f'PRAGMA table_info("{table}")').fetchall()]
            for col in columns:
                matches = cur.execute(f'SELECT "{col}" FROM "{table}" WHERE LOWER(CAST("{col}" AS TEXT)) LIKE "%gmail%" OR LOWER(CAST("{col}" AS TEXT)) LIKE "%luislazober%"').fetchall()
                if matches:
                    print(f"Found match in {table}.{col}: {matches}")
        except Exception as e:
            print(f"Error checking {table}: {e}")
else:
    print("VRT.db not found")
