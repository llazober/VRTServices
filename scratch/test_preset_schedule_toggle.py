import sys
import os
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()
sys.path.append(".")

from app import create_customer, get_db_connection
from psycopg2.extras import RealDictCursor
from starlette.requests import Request

class DummyRequest:
    def __init__(self, json_data, username="admin"):
        self._json = json_data
        self.state = type('State', (), {'username': username})()
        self.cookies = {"access_token": "valid_token"}

    async def json(self):
        return self._json

def test_preset_schedule_toggle():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Clean up test customers if exist
            test_numbers = ["CUST-TEST-OPT-TRUE", "CUST-TEST-OPT-FALSE"]
            for num in test_numbers:
                cur.execute("SELECT id FROM customer WHERE custumer_number = %s;", (num,))
                rec = cur.fetchone()
                if rec:
                    cid = rec["id"]
                    cur.execute("DELETE FROM compliance_calendar_events WHERE customer_id = %s;", (cid,))
                    cur.execute("DELETE FROM customer_billing_schedules WHERE customer_id = %s;", (cid,))
                    cur.execute("DELETE FROM customer WHERE id = %s;", (cid,))
            conn.commit()

        # Test Case 1: create_preset_schedule = False
        payload_false = {
            "custumer_number": "CUST-TEST-OPT-FALSE",
            "customer_type": "Business",
            "legal_name": "Test Sched False LLC",
            "create_preset_schedule": False
        }
        
        print("Testing create_customer with create_preset_schedule = False...")
        req_false = DummyRequest(payload_false)
        res_false = asyncio.run(create_customer(req_false))
        print("Result False:", res_false)
        cid_false = res_false["customer"]["id"]

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM compliance_calendar_events WHERE customer_id = %s;", (cid_false,))
            count_false = cur.fetchone()["count"]
            print(f"Events created when create_preset_schedule=False: {count_false}")
            assert count_false == 0, f"Expected 0 events when create_preset_schedule=False, got {count_false}"

        # Test Case 2: create_preset_schedule = True
        payload_true = {
            "custumer_number": "CUST-TEST-OPT-TRUE",
            "customer_type": "Business",
            "legal_name": "Test Sched True LLC",
            "create_preset_schedule": True
        }
        print("Testing create_customer with create_preset_schedule = True...")
        req_true = DummyRequest(payload_true)
        res_true = asyncio.run(create_customer(req_true))
        print("Result True:", res_true)
        cid_true = res_true["customer"]["id"]

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM compliance_calendar_events WHERE customer_id = %s;", (cid_true,))
            count_true = cur.fetchone()["count"]
            print(f"Events created when create_preset_schedule=True: {count_true}")
            assert count_true > 0, f"Expected >0 events when create_preset_schedule=True, got {count_true}"

        # Clean up test records
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for cid in [cid_false, cid_true]:
                cur.execute("DELETE FROM compliance_calendar_events WHERE customer_id = %s;", (cid,))
                cur.execute("DELETE FROM customer_billing_schedules WHERE customer_id = %s;", (cid,))
                cur.execute("DELETE FROM customer WHERE id = %s;", (cid,))
            conn.commit()

        print("\nALL PRESET SCHEDULE TOGGLE TESTS PASSED SUCCESSFULLY!")

    finally:
        conn.close()

if __name__ == "__main__":
    test_preset_schedule_toggle()
