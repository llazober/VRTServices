import os, json, boto3
from app import get_db_connection, get_s3_client, DO_SPACES_BUCKET

conn = get_db_connection()
with conn.cursor() as cur:
    # Update customer legal_name if needed and fix do_folder_path
    cur.execute("SELECT id, legal_name, parent_name, do_folder_path FROM customer WHERE legal_name ILIKE '%BARCELONA%';")
    rows = cur.fetchall()
    print("BARCELONA Customers:", rows)

    # Check communications for BARCELONA LLC
    cur.execute("""
        SELECT id, attachments_json FROM customer_communications 
        WHERE attachments_json::text LIKE '%BARCAELONA%';
    """)
    comms = cur.fetchall()
    print("Mismatched Comms:", comms)

client, err = get_s3_client()
if client:
    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
    # Copy S3 object from BARCAELONA to BARCELONA
    old_key = "Datalazo LLC/BARCAELONA  LLC/Inbox/Document (22) (1) (6).pdf"
    new_key = "Datalazo LLC/BARCELONA LLC/Inbox/Document (22) (1) (6).pdf"
    try:
        client.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': old_key}, Key=new_key, ACL='private')
        print(f"Copied {old_key} -> {new_key}")
        # Update comms DB
        with conn.cursor() as cur:
            cur.execute("UPDATE customer_communications SET attachments_json = %s WHERE id = 92;", (json.dumps([new_key]),))
            conn.commit()
            print("Updated comms ID 92")
    except Exception as e:
        print("S3 copy error:", e)
conn.close()
