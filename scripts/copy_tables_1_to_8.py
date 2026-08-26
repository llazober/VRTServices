import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_TABLES = [
    "customer",
    "customer_communications",
    "customer_task_checklist",
    "webhook_debug_log",
    "ClientChartOfAccounts",
    "ClientTransactionHistory",
    "ParentClientMap",
    "QboConnection"
]

def get_db_urls():
    src_url = os.environ.get("DATABASE_URL") or "postgresql://postgres:Paris2025%24@161.35.119.223:5432/datalazo?sslmode=disable"
    if "/datalazo" in src_url:
        tgt_url = src_url.replace("/datalazo", "/VRT")
    else:
        tgt_url = "postgresql://postgres:Paris2025%24@161.35.119.223:5432/VRT?sslmode=disable"
    return src_url, tgt_url

def migrate_tables_1_to_8():
    src_url, tgt_url = get_db_urls()
    print("Connecting to Source DB (datalazo)...")
    conn_src = psycopg2.connect(src_url)
    print("Connecting to Target DB (VRT)...")
    conn_tgt = psycopg2.connect(tgt_url)

    # Clean drop target tables 5, 6, 7 if their column types were mismatched
    with conn_tgt.cursor() as cur_tgt:
        cur_tgt.execute('DROP TABLE IF EXISTS "ClientChartOfAccounts", "ClientTransactionHistory", "ParentClientMap" CASCADE;')
        conn_tgt.commit()

    print("\n--- Migrating Tables 1 to 8 ---")
    for tbl in TARGET_TABLES:
        tbl_quoted = f'"{tbl}"' if any(c.isupper() for c in tbl) else tbl
        print(f"\nProcessing '{tbl}'...")
        
        try:
            # 1. Inspect source columns
            with conn_src.cursor(cursor_factory=RealDictCursor) as cur_src:
                cur_src.execute("""
                    SELECT column_name, data_type, udt_name, is_nullable, column_default, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (tbl,))
                cols_meta = cur_src.fetchall()

            if not cols_meta:
                print(f"⚠️ Table '{tbl}' not found in source schema.")
                continue

            # 2. Build & execute CREATE TABLE DDL dynamically matching source datalazo exact types
            col_defs = []
            for col in cols_meta:
                c_name = f'"{col["column_name"]}"'
                raw_type = col["data_type"].upper()
                udt = col["udt_name"].upper()
                
                if raw_type == "CHARACTER VARYING":
                    max_len = col.get("character_maximum_length")
                    c_type = f"VARCHAR({max_len})" if max_len else "VARCHAR"
                elif raw_type in ["USER-DEFINED", "ARRAY"]:
                    c_type = udt
                else:
                    c_type = raw_type
                
                c_default = col["column_default"]
                if col["column_name"] == 'id' and c_default and "nextval" in str(c_default):
                    c_def = f"{c_name} BIGSERIAL PRIMARY KEY"
                elif col["column_name"] == 'id':
                    c_def = f"{c_name} {c_type} PRIMARY KEY"
                else:
                    c_def = f"{c_name} {c_type}"
                    if col["is_nullable"] == "NO" and not (c_default and "nextval" in str(c_default)):
                        c_def += " NOT NULL"
                col_defs.append(c_def)

            create_sql = f"CREATE TABLE IF NOT EXISTS {tbl_quoted} (\n  " + ",\n  ".join(col_defs) + "\n);"
            
            with conn_tgt.cursor() as cur_tgt:
                cur_tgt.execute(create_sql)
                conn_tgt.commit()

            # Ensure any missing columns in target are added
            with conn_tgt.cursor(cursor_factory=RealDictCursor) as cur_tgt:
                cur_tgt.execute("""
                    SELECT column_name FROM information_schema.columns WHERE table_name = %s;
                """, (tbl,))
                tgt_cols = {r["column_name"] for r in cur_tgt.fetchall()}

            for col in cols_meta:
                if col["column_name"] not in tgt_cols:
                    c_name = f'"{col["column_name"]}"'
                    raw_type = col["data_type"].upper()
                    udt = col["udt_name"].upper()
                    if raw_type == "CHARACTER VARYING":
                        max_len = col.get("character_maximum_length")
                        c_type = f"VARCHAR({max_len})" if max_len else "VARCHAR"
                    elif raw_type in ["USER-DEFINED", "ARRAY"]:
                        c_type = udt
                    else:
                        c_type = raw_type
                    alter_sql = f"ALTER TABLE {tbl_quoted} ADD COLUMN {c_name} {c_type};"
                    with conn_tgt.cursor() as cur_tgt:
                        cur_tgt.execute(alter_sql)
                        conn_tgt.commit()

            # 3. Fetch source data
            with conn_src.cursor(cursor_factory=RealDictCursor) as cur_src:
                cur_src.execute(f"SELECT * FROM {tbl_quoted};")
                rows = cur_src.fetchall()

            if not rows:
                print(f"  • {tbl}: Schema ready, 0 source rows to copy.")
                continue

            # 4. Insert data into VRT target table
            columns = list(rows[0].keys())
            cols_str = ", ".join([f'"{c}"' for c in columns])
            val_placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO {tbl_quoted} ({cols_str}) VALUES ({val_placeholders}) ON CONFLICT DO NOTHING;"

            with conn_tgt.cursor() as cur_tgt:
                inserted_count = 0
                for r in rows:
                    row_vals = []
                    for c in columns:
                        v = r[c]
                        if isinstance(v, (dict, list)):
                            v = json.dumps(v)
                        row_vals.append(v)
                    cur_tgt.execute(insert_sql, tuple(row_vals))
                    inserted_count += cur_tgt.rowcount
                conn_tgt.commit()

            print(f"  ✓ {tbl}: Successfully copied {len(rows)} records to VRT database.")

            # 5. Reset sequence if table has autoincrement sequence on id column
            if "id" in columns:
                with conn_tgt.cursor() as cur_tgt:
                    try:
                        cur_tgt.execute(f"SELECT setval(pg_get_serial_sequence('{tbl_quoted}', 'id'), COALESCE(MAX(id), 1)) FROM {tbl_quoted};")
                        conn_tgt.commit()
                    except Exception:
                        conn_tgt.rollback()

        except Exception as e:
            conn_tgt.rollback()
            print(f"❌ Error migrating table '{tbl}': {e}")

    # Final Verification Report
    print("\n--- FINAL VERIFICATION REPORT ---")
    print(f"{'Table Name':<32} | {'datalazo Rows':<15} | {'VRT Rows':<10} | {'Status':<10}")
    print("-" * 75)
    for tbl in TARGET_TABLES:
        tbl_quoted = f'"{tbl}"' if any(c.isupper() for c in tbl) else tbl
        try:
            with conn_src.cursor() as cur_src:
                cur_src.execute(f"SELECT COUNT(*) FROM {tbl_quoted};")
                c_src = cur_src.fetchone()[0]

            with conn_tgt.cursor() as cur_tgt:
                cur_tgt.execute(f"SELECT COUNT(*) FROM {tbl_quoted};")
                c_tgt = cur_tgt.fetchone()[0]

            status = "MATCH ✓" if c_src == c_tgt else "MISMATCH ⚠️"
            print(f"{tbl:<32} | {c_src:<15} | {c_tgt:<10} | {status:<10}")
        except Exception as ve:
            conn_tgt.rollback()
            print(f"{tbl:<32} | ERROR: {ve}")

    conn_src.close()
    conn_tgt.close()

if __name__ == "__main__":
    migrate_tables_1_to_8()
