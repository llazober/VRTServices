import sys
import psycopg2

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def rename_datalazo_tables():
    src_url = "postgresql://postgres:Paris2025%24@161.35.119.223:5432/datalazo?sslmode=disable"
    print("Connecting to datalazo database...")
    conn = psycopg2.connect(src_url)
    
    tables_to_rename = [
        ("customer", "customer_old"),
        ("customer_communications", "customer_communications_old"),
        ("customer_task_checklist", "customer_task_checklist_old"),
        ("webhook_debug_log", "webhook_debug_log_old"),
        ('"ClientChartOfAccounts"', 'ClientChartOfAccounts_old'),
        ('"ClientTransactionHistory"', 'ClientTransactionHistory_old'),
        ('"ParentClientMap"', 'ParentClientMap_old'),
        ('"QboConnection"', 'QboConnection_old')
    ]
    
    for old_name, new_name in tables_to_rename:
        with conn.cursor() as cur:
            try:
                cur.execute(f"ALTER TABLE {old_name} RENAME TO {new_name};")
                conn.commit()
                print(f"✓ Renamed '{old_name}' -> '{new_name}' in datalazo DB.")
            except Exception as e:
                conn.rollback()
                print(f"⚠️ Notice renaming '{old_name}': {e}")
                
    conn.close()

if __name__ == "__main__":
    rename_datalazo_tables()
