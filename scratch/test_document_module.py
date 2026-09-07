import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_document_module():
    from app import get_db_connection, init_document_tables
    from psycopg2.extras import RealDictCursor

    print("[TEST] Initializing document tables...")
    init_document_tables()

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, title, rel_path, category FROM document ORDER BY id ASC;")
        docs = cur.fetchall()
        print(f"[TEST] Found {len(docs)} documents in 'document' table:")
        for d in docs:
            print(f"  - ID: {d['id']} | Title: {d['title']} | Path: {d['rel_path']}")

        cur.execute("SELECT id, document_id, chunk_index, length(content) as len FROM document_chunk ORDER BY id ASC;")
        chunks = cur.fetchall()
        print(f"[TEST] Found {len(chunks)} chunks in 'document_chunk' table:")
        for c in chunks:
            print(f"  - Chunk ID: {c['id']} | Doc ID: {c['document_id']} | Index: {c['chunk_index']} | Length: {c['len']}")

    conn.close()

if __name__ == "__main__":
    test_document_module()
