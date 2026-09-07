import sys
from dotenv import load_dotenv
load_dotenv()
import psycopg2
from psycopg2.extras import RealDictCursor
sys.path.append(".")
from app import get_db_connection, generate_preset_compliance_events_for_customer

def test_preset_schedule_lifecycle():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Create temporary test customer
            test_number = "TEST-SCHED-9999"
            legal_name = "Test Schedule Customer LLC"
            customer_type = "Business"
            
            # Clean up if previously exists
            cur.execute("SELECT id FROM customer WHERE custumer_number = %s;", (test_number,))
            existing = cur.fetchone()
            if existing:
                cid = existing["id"]
                cur.execute("DELETE FROM compliance_calendar_events WHERE customer_id = %s;", (cid,))
                cur.execute("DELETE FROM customer_billing_schedules WHERE customer_id = %s;", (cid,))
                cur.execute("DELETE FROM customer WHERE id = %s;", (cid,))
                conn.commit()

            cur.execute("""
                INSERT INTO customer (
                    custumer_number, customer_type, legal_name, display_name, status, parent_name, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, 'Active', 'VRT Services', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id;
            """, (test_number, customer_type, legal_name, legal_name))
            new_cust = cur.fetchone()
            cust_id = new_cust["id"]
            
            # Generate preset schedule
            count = generate_preset_compliance_events_for_customer(cur, cust_id, customer_type, "Mary")
            conn.commit()
            
            print(f"Created customer #{cust_id} and generated {count} preset schedule events.")
            
            # Verify events exist in DB
            cur.execute("SELECT COUNT(*) FROM compliance_calendar_events WHERE customer_id = %s;", (cust_id,))
            event_count = cur.fetchone()["count"]
            assert event_count == count, f"Expected {count} events, found {event_count}"
            print(f"Verified {event_count} events exist for customer #{cust_id}.")

            # 2. Test Deletion logic
            cur.execute("DELETE FROM compliance_calendar_events WHERE customer_id = %s;", (cust_id,))
            cur.execute("DELETE FROM customer_billing_schedules WHERE customer_id = %s;", (cust_id,))
            cur.execute("DELETE FROM customer_invoices WHERE customer_id = %s;", (cust_id,))
            cur.execute("DELETE FROM customer WHERE id = %s;", (cust_id,))
            conn.commit()

            # Verify events deleted
            cur.execute("SELECT COUNT(*) FROM compliance_calendar_events WHERE customer_id = %s;", (cust_id,))
            after_del_count = cur.fetchone()["count"]
            assert after_del_count == 0, f"Expected 0 events after delete, found {after_del_count}"
            print(f"Verified schedule events were successfully deleted for customer #{cust_id}.")
            print("ALL PRESET SCHEDULE LIFECYCLE TESTS PASSED SUCCESSFULLY!")
    finally:
        conn.close()

if __name__ == "__main__":
    test_preset_schedule_lifecycle()
