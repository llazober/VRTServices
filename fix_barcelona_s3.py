import os, json
from app import get_db_connection, get_s3_client, DO_SPACES_BUCKET

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        UPDATE customer 
        SET legal_name = 'BARCELONA LLC', do_folder_path = 'Datalazo LLC/BARCELONA LLC/' 
        WHERE id = 9;
    """)
    conn.commit()
    print("[DB SUCCESS] Updated customer 9 DB record to 'BARCELONA LLC' and 'Datalazo LLC/BARCELONA LLC/'")

client, err = get_s3_client()
if client:
    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
    target_key = "Datalazo LLC/BARCELONA LLC/Inbox/Document (22) (1) (6).pdf"

    # List all objects in bucket matching BARCELONA or BARCAELONA
    resp = client.list_objects_v2(Bucket=bucket, Prefix="Datalazo LLC/")
    for obj in resp.get('Contents', []):
        key = obj['Key']
        if ('BARCELONA' in key.upper() or 'BARCAELONA' in key.upper()) and 'Document (22) (1) (6).pdf' in key:
            print(f"Found S3 Key: {key}")
            try:
                client.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': key}, Key=target_key, ACL='private')
                print(f"[S3 SUCCESS] Copied '{key}' -> '{target_key}'")
            except Exception as e_copy:
                print(f"Copy error for {key}: {e_copy}")

    # Update customer_communications ID 92
    with conn.cursor() as cur:
        cur.execute("UPDATE customer_communications SET attachments_json = %s WHERE id = 92;", (json.dumps([target_key]),))
        conn.commit()
        print("[DB SUCCESS] Updated customer_communications ID 92 attachments_json to target_key")

conn.close()
