import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Migrate all database tables from datalazo to VRT so VRT is a complete standalone tenant DB
ALL_TABLES = [
    "customer",
    "customer_communications",
    "customer_task_checklist",
    "webhook_debug_log",
    "ClientChartOfAccounts",
    "ClientTransactionHistory",
    "ParentClientMap",
    "QboConnection",
    "ClientUser",
    "ClientUserLogin",
    "LoginLog",
    "Document",
    "DocumentChunk",
    "Settings",
    "TokenUsage",
    "Invoice",
    "Client",
    "Appointment",
    "Lead",
    "MarketingLead",
    "Keyword"
]

def get_db_urls():
    src_url = "postgresql://postgres:Paris2025%24@161.35.119.223:5432/datalazo?sslmode=disable"
    tgt_url = "postgresql://postgres:Paris2025%24@161.35.119.223:5432/VRT?sslmode=disable"
    return src_url, tgt_url

def migrate_all_tables():
    src_url, tgt_url = get_db_urls()
    print("Connecting to Source DB (datalazo)...")
    conn_src = psycopg2.connect(src_url)
    print("Connecting to Target DB (VRT)...")
    conn_tgt = psycopg2.connect(tgt_url)

    print("\n--- Syncing All Application Tables to VRT Database ---")
    for tbl in ALL_TABLES:
        tbl_quoted = f'"{tbl}"' if any(c.isupper() for c in tbl) else tbl
        
        try:
            # 1. Inspect source columns (check if original table or _old table exists in datalazo)
            with conn_src.cursor(cursor_factory=RealDictCursor) as cur_src:
                cur_src.execute("""
                    SELECT column_name, data_type, udt_name, is_nullable, column_default, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s OR table_name = %s
                    ORDER BY ordinal_position;
                """, (tbl, f"{tbl}_old"))
                cols_meta = cur_src.fetchall()

            if not cols_meta:
                print(f"• Table '{tbl}': Not found in source schema, skipping.")
                continue

            # Determine actual source table name (tbl or tbl_old)
            with conn_src.cursor() as cur_src:
                cur_src.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND (table_name = %s OR table_name = %s);
                """, (tbl, f"{tbl}_old"))
                src_tbl_real = cur_src.fetchone()[0]
                src_tbl_quoted = f'"{src_tbl_real}"' if any(c.isupper() for c in src_tbl_real) else src_tbl_real

            # 2. Build & execute CREATE TABLE DDL dynamically matching source exact types
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

            # Ensure missing columns in target are added
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
                cur_src.execute(f"SELECT * FROM {src_tbl_quoted};")
                rows = cur_src.fetchall()

            if not rows:
                print(f"  • {tbl}: Schema ready in VRT, 0 source rows.")
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

            print(f"  ✓ {tbl}: Synced {len(rows)} records into VRT database.")

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
            print(f"❌ Error syncing table '{tbl}': {e}")

    # Final Verification Report for VRT DB
    print("\n--- FINAL VERIFICATION REPORT (VRT DB) ---")
    print(f"{'Table Name':<32} | {'VRT Record Count':<18} | {'Status':<10}")
    print("-" * 65)
    for tbl in ALL_TABLES:
        tbl_quoted = f'"{tbl}"' if any(c.isupper() for c in tbl) else tbl
        try:
            with conn_tgt.cursor() as cur_tgt:
                cur_tgt.execute(f"SELECT COUNT(*) FROM {tbl_quoted};")
                c_tgt = cur_tgt.fetchone()[0]

            print(f"{tbl:<32} | {c_tgt:<18} | OK ✓")
        except Exception as ve:
            conn_tgt.rollback()
            print(f"{tbl:<32} | NOT PRESENT        | ⚠️")

    conn_src.close()
    conn_tgt.close()

if __name__ == "__main__":
    migrate_all_tables()
