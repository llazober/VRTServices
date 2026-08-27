import sys
import psycopg2

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def cleanup_databases():
    import os
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is missing.")
    vrt_url = db_url if "/VRT" in db_url else db_url.replace("/datalazo", "/VRT")
    print("Connecting to VRT database...")
    conn_vrt = psycopg2.connect(vrt_url)
    
    tables_to_drop_from_vrt = [
        '"ClientUser"', '"ClientUserLogin"', '"LoginLog"', '"Document"',
        '"DocumentChunk"', '"Settings"', '"TokenUsage"', '"Invoice"',
        '"Client"', '"Appointment"', '"Lead"', '"MarketingLead"', '"Keyword"'
    ]
    
    with conn_vrt.cursor() as cur:
        for tbl in tables_to_drop_from_vrt:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE;")
                conn_vrt.commit()
                print(f"✓ Dropped table {tbl} from VRT database.")
            except Exception as e:
                conn_vrt.rollback()
                print(f"Notice dropping {tbl}: {e}")
                
    conn_vrt.close()

    # 2. Connect to datalazo and fix casing of renamed _old tables
    dlz_url = db_url if "/datalazo" in db_url else db_url.replace("/VRT", "/datalazo")
    print("\nConnecting to datalazo database...")
    conn_dlz = psycopg2.connect(dlz_url)
    
    casing_fixes = [
        ("clientchartofaccounts_old", '"ClientChartOfAccounts_old"'),
        ("clienttransactionhistory_old", '"ClientTransactionHistory_old"'),
        ("parentclientmap_old", '"ParentClientMap_old"'),
        ("qboconnection_old", '"QboConnection_old"')
    ]
    
    with conn_dlz.cursor() as cur:
        for old_lc, new_case in casing_fixes:
            try:
                cur.execute(f"ALTER TABLE {old_lc} RENAME TO {new_case};")
                conn_dlz.commit()
                print(f"✓ Fixed casing: {old_lc} -> {new_case}")
            except Exception as e:
                conn_dlz.rollback()
                print(f"Notice fixing casing for {old_lc}: {e}")
                
    conn_dlz.close()

if __name__ == "__main__":
    cleanup_databases()
