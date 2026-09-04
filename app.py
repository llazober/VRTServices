import os
# Updated server routes & templates - fixed HTML string escaping for customer names



try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass
import datetime
import time
import secrets
import shutil
import tempfile
import base64
import json
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import hmac
import psycopg2
import email.utils
import re
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
import traceback
from extractor import run_extraction, extract_check_images

app = FastAPI(title="Bank Statement OCR Extractor")

@app.middleware("http")
async def add_security_and_cache_headers(request: Request, call_next):
    # Enforce HTTPS redirect if request came in via plain HTTP
    proto = request.headers.get("x-forwarded-proto", "").lower()
    if proto == "http":
        url = request.url.replace(scheme="https")
        red_resp = RedirectResponse(url=str(url), status_code=301)
        red_resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        red_resp.headers["X-Content-Type-Options"] = "nosniff"
        red_resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        red_resp.headers["X-XSS-Protection"] = "1; mode=block"
        red_resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        red_resp.headers["Content-Security-Policy"] = "default-src 'self' https: data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: blob: https:; font-src 'self' https: data:; connect-src 'self' https:;"
        red_resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return red_resp

    response = await call_next(request)
    # Security headers for SecurityHeaders.com / SSL Labs A+ rating
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self' https: data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: blob: https:; font-src 'self' https: data:; connect-src 'self' https:;"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    
    if request.url.path in ["/", "/index", "/dashboard", "/customers"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[UNHANDLED EXCEPTION]: {exc}")
    traceback.print_exc()
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(exc)}"}
        )
    return HTMLResponse(
        status_code=500,
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Internal Server Error - Datalazo CRM</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 40px; max-width: 500px; width: 90%; text-align: center; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
                h1 {{ color: #f43f5e; margin-top: 0; font-size: 24px; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }}
                .btn {{ background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; text-decoration: none; cursor: pointer; display: inline-block; }}
                .btn:hover {{ background: #2563eb; }}
                .err-box {{ background: #0f172a; border: 1px solid #334155; color: #f87171; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; text-align: left; overflow-x: auto; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Something Went Wrong</h1>
                <p>An internal server error occurred while processing your request. Please try reloading or returning to the dashboard.</p>
                <div class="err-box">{str(exc)}</div>
                <a href="/dashboard" class="btn">Reload Dashboard</a>
            </div>
        </body>
        </html>
        """
    )

# ── Auth config ────────────────────────────────────────────────────────────────
APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
COOKIE_NAME  = "ocr_session"

# ── Dynamic CSV Export Layout Config ───────────────────────────────────────────
DEFAULT_CSV_MAPPING = {
    "headers": ["Type", "Date", "Entity Code", "Account", "Debit", "Credit", "Description", "Reference"],
    "fields": [
        {"header": "Type", "type": "constant", "value": "GJ"},
        {"header": "Date", "type": "field", "source": "date"},
        {"header": "Entity Code", "type": "constant", "value": ""},
        {"header": "Account", "type": "account_mapping", "debit_value": "260", "credit_value": "500"},
        {"header": "Debit", "type": "debit"},
        {"header": "Credit", "type": "credit"},
        {"header": "Description", "type": "field", "source": "description", "max_length": 98},
        {"header": "Reference", "type": "reference"}
    ]
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datalazo.config.json")
def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

APP_CONFIG = load_config()

def parse_clean_email(email_str: str) -> str:
    """Extract clean, raw email address from potential RFC email header strings e.g. 'John <john@domain.com>' -> 'john@domain.com'."""
    if not email_str:
        return ""
    s = str(email_str).strip().strip("[]'\"` ")
    # First attempt direct regex extraction for explicit email patterns
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', s)
    if match:
        return match.group(0).strip()
    name, addr = email.utils.parseaddr(s)
    if addr and "@" in addr:
        return addr.strip()
    return s

def get_resend_to_email() -> str:
    """Fetch target recipient email for system/support alerts, checking multiple env var aliases."""
    val = (
        os.environ.get("RESEND_TO_EMAIL") or
        os.environ.get("RESEND_TO") or
        os.environ.get("TO_EMAIL") or
        os.environ.get("SUPPORT_EMAIL") or
        os.environ.get("resend_to_email") or
        os.environ.get("resend_to-email") or
        os.environ.get("RESEND_TO-EMAIL") or
        "luislazober@gmail.com"
    )
    cleaned = parse_clean_email(val)
    return cleaned if cleaned else "luislazober@gmail.com"

def parse_reply_to_list(val) -> list[str]:
    """Parse single or multiple comma-separated reply-to email addresses into a list of clean email strings."""
    if not val:
        return ["vrt@ostooechei.resend.app"]
    if isinstance(val, list):
        items = val
    else:
        items = str(val).replace(";", ",").split(",")
    
    cleaned_list = []
    for item in items:
        cleaned = parse_clean_email(item)
        if cleaned and "receive.datalazo.net" not in cleaned.lower():
            if cleaned not in cleaned_list:
                cleaned_list.append(cleaned)
    return cleaned_list if cleaned_list else ["vrt@ostooechei.resend.app"]

def get_resend_from_email() -> str:
    """Fetch clean from email address, checking multiple env var aliases."""
    raw = (
        os.environ.get("RESEND_FROM_EMAIL") or
        os.environ.get("FROM_EMAIL") or
        os.environ.get("SENDER_EMAIL") or
        os.environ.get("resend_from_email") or
        "notification@vrtservices12.com"
    ).strip().strip('\'"')
    cleaned = parse_clean_email(raw)
    if cleaned and len(cleaned) > 3:
        return cleaned
    return "notification@vrtservices12.com"

def format_resend_from_header(display_name: str = "") -> str:
    """Format full RFC email 'From' string e.g. 'VRT Services Portal <notification@vrtservices12.com>'."""
    clean_addr = get_resend_from_email()
    name = (display_name or "").strip()
    if not name or name.lower() == clean_addr.lower() or "@" in name:
        name = "VRT Services Portal"
    return f"{name} <{clean_addr}>"

def get_resend_reply_to_email() -> str:
    """Fetch reply-to email string (comma-separated if multiple) for UI templates and environment lookups."""
    val = (
        os.environ.get("RESEND_REPLY_TO_EMAIL") or
        os.environ.get("RESEND_REPLY_TO") or
        os.environ.get("REPLY_TO_EMAIL") or
        os.environ.get("REPLY_TO") or
        os.environ.get("resend_reply_to_email") or
        os.environ.get("resend_reply_to-email") or
        os.environ.get("RESEND_REPLY_TO-EMAIL") or
        "vrt@ostooechei.resend.app"
    )
    res_list = parse_reply_to_list(val)
    return ", ".join(res_list)

# Session tracking:
# valid_sessions: token -> {"username": str}
# active_user_tokens: username -> token (Enforces single active instance per user)
valid_sessions: dict[str, dict] = {}
active_user_tokens: dict[str, str] = {}

def create_user_session(username: str) -> str:
    """Creates a new session token, invalidating any previous session for the username."""
    username_clean = username.strip()
    old_token = active_user_tokens.get(username_clean)
    if old_token:
        valid_sessions.pop(old_token, None)

    token = secrets.token_urlsafe(32)
    valid_sessions[token] = {
        "username": username_clean
    }
    active_user_tokens[username_clean] = token

    # Persist session token in database so server redeployments/restarts keep users logged in
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE "ClientUser" SET "sessionToken" = %s WHERE username = %s;',
                (token, username_clean)
            )
            conn.commit()
    except Exception as e:
        print(f"Database error updating sessionToken: {e}")
    finally:
        if conn:
            conn.close()

    return token

def get_current_session_info(request: Request) -> tuple[str | None, str | None, str | None]:
    """
    Validates cookie token. Checks:
    1. Token existence in valid_sessions
    2. Single active instance rule (active_user_tokens[username] == token)
    3. Database fallback lookup across server restarts

    Returns (token, username, invalid_reason).
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None, None, None

    sess = valid_sessions.get(token)
    if sess:
        username = sess.get("username")
        if active_user_tokens.get(username) == token:
            return token, username, None

    # Fallback lookup in DB if server was restarted and in-memory dicts were reset
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT username FROM "ClientUser" WHERE "sessionToken" = %s;', (token,))
            user = cur.fetchone()
            if user and user.get("username"):
                username_clean = user.get("username")
                valid_sessions[token] = {"username": username_clean}
                active_user_tokens[username_clean] = token
                return token, username_clean, None
    except Exception as e:
        pass
    finally:
        if conn:
            conn.close()

    return None, None, "Your account was logged in from another device or location."

def get_current_session(request: Request) -> str | None:
    token, _, _ = get_current_session_info(request)
    return token

def get_current_username(request: Request) -> str | None:
    _, username, _ = get_current_session_info(request)
    return username

def require_auth(request: Request):
    """Redirect to login if not authenticated or not allowed on site."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    allowed, _ = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=303, headers={"Location": "/login"})

# ── Site validation helpers ───────────────────────────────────────────────────
def get_request_host(request: Request) -> str:
    """Extract and normalize host domain from Request (handles X-Forwarded-Host and Host headers)."""
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        host = forwarded.split(",")[0].strip()
    else:
        host = request.headers.get("host", "")
    return host.split(":")[0].strip().lower()

def is_private_ip(ip: str) -> bool:
    if not ip:
        return True
    clean_ip = ip.strip().replace("::ffff:", "")
    if clean_ip in ("127.0.0.1", "::1", "localhost"):
        return True
    parts = clean_ip.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        p0, p1 = int(parts[0]), int(parts[1])
        if p0 == 10:
            return True
        if p0 == 172 and 16 <= p1 <= 31:
            return True
        if p0 == 192 and p1 == 168:
            return True
        if p0 == 169 and p1 == 254:
            return True
        if p0 == 127:
            return True
    return False

def get_real_client_ip(request: Request) -> str:
    """Extract real client IP address, handling Cloudflare, proxies, and filtering private IPs (like 10.1.0.10)."""
    candidates = []

    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        candidates.append(cf_ip)

    true_client_ip = request.headers.get("true-client-ip")
    if true_client_ip:
        candidates.append(true_client_ip)

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        candidates.append(x_real_ip)

    x_client_ip = request.headers.get("x-client-ip")
    if x_client_ip:
        candidates.append(x_client_ip)

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        for ip in x_forwarded_for.split(","):
            candidates.append(ip.strip())

    if request.client and request.client.host:
        candidates.append(request.client.host)

    for raw_ip in candidates:
        clean = raw_ip.strip().replace("::ffff:", "")
        if clean and not is_private_ip(clean):
            return clean

    for raw_ip in candidates:
        clean = raw_ip.strip().replace("::ffff:", "")
        if clean:
            return clean

    return "127.0.0.1"

def is_user_allowed_on_site(username: str, request: Request) -> tuple[bool, str]:
    """
    Checks if the given user is allowed to log in or access the application on the current request host.
    Returns (is_allowed: bool, assigned_subdomain: str).
    """
    request_host = get_request_host(request)

    # Allow local development/testing host names
    if request_host in ("localhost", "127.0.0.1", "testserver"):
        return True, ""

    # Allow default admin user across domains
    if APP_USERNAME and username.lower() == APP_USERNAME.lower():
        return True, ""

    assigned = get_user_assigned_subdomain(username)
    if not assigned:
        return True, ""

    assigned_subdomain = assigned.strip().lower()

    # Exact match (e.g. ocr.datalazo.net == ocr.datalazo.net)
    if request_host == assigned_subdomain:
        return True, assigned_subdomain

    # If assigned_subdomain is just the prefix (e.g. 'ocr')
    if "." not in assigned_subdomain:
        if request_host == assigned_subdomain or request_host.startswith(assigned_subdomain + "."):
            return True, assigned_subdomain

    # If request_host or assigned_subdomain are subdomains of each other
    if request_host.endswith("." + assigned_subdomain) or assigned_subdomain.endswith("." + request_host):
        return True, assigned_subdomain

    return False, assigned_subdomain

# ── Templates ──────────────────────────────────────────────────────────────────
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# ── Helpers ────────────────────────────────────────────────────────────────────
def cleanup_temp_dir(path: str):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"Cleaned up temporary directory: {path}")
        except Exception as e:
            print(f"Failed to clean up temporary directory {path}: {e}")

# ── DB & Password helpers ──────────────────────────────────────────────────────
def get_db_connection(db_name: str = None):
    """
    Returns a PostgreSQL connection. Supports multi-tenant routing by db_name.
    Defaults to the primary VRT database.
    """
    target_db = db_name or os.environ.get("POSTGRES_DB") or "VRT"
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        new_path = f"/{target_db}"
        db_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
    else:
        raise ValueError("DATABASE_URL environment variable is missing. Please set DATABASE_URL in your environment or .env file.")
    return psycopg2.connect(db_url)

def sync_customer_parent_mapping(cur, parent_name: str, legal_name: str, display_name: str = None):
    """Ensure parent-client mapping exists in ParentClientMap using legal_name under parent_name."""
    if not parent_name or not parent_name.strip() or not legal_name or not legal_name.strip():
        return
    import uuid
    p_name = parent_name.strip()
    l_name = legal_name.strip()

    cur.execute('''
        INSERT INTO "ParentClientMap" ("id", "parentName", "clientName", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT ("parentName", "clientName")
        DO UPDATE SET "updatedAt" = CURRENT_TIMESTAMP;
    ''', (str(uuid.uuid4()), p_name, l_name))

def delete_customer_parent_mapping(cur, parent_name: str, legal_name: str, display_name: str = None):
    """Remove parent-client mapping and associated client data (COA & Vendor rules) when a customer is deleted."""
    if not legal_name or not legal_name.strip():
        return
    l_name = legal_name.strip()
    d_name = (display_name or "").strip()
    p_name = (parent_name or "").strip()

    # 1. Delete mapping entry from ParentClientMap
    cur.execute('''
        DELETE FROM "ParentClientMap"
        WHERE (LOWER("clientName") = LOWER(%s) OR (LOWER("clientName") = LOWER(%s) AND %s != ''))
          AND (%s = '' OR LOWER("parentName") = LOWER(%s) OR "parentName" IS NULL OR "parentName" = '');
    ''', (l_name, d_name, d_name, p_name, p_name))

    # 2. Clean up associated Chart of Accounts entries
    cur.execute('''
        DELETE FROM "ClientChartOfAccounts"
        WHERE (LOWER("clientName") = LOWER(%s) OR (LOWER("clientName") = LOWER(%s) AND %s != ''))
          AND (%s = '' OR LOWER("parentName") = LOWER(%s) OR "parentName" IS NULL OR "parentName" = '');
    ''', (l_name, d_name, d_name, p_name, p_name))

    # 3. Clean up associated Vendor Transaction History rules
    cur.execute('''
        DELETE FROM "ClientTransactionHistory"
        WHERE (LOWER("clientName") = LOWER(%s) OR (LOWER("clientName") = LOWER(%s) AND %s != ''))
          AND (%s = '' OR LOWER("parentName") = LOWER(%s) OR "parentName" IS NULL OR "parentName" = '');
    ''', (l_name, d_name, d_name, p_name, p_name))

def init_customer_table():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    id              BIGSERIAL PRIMARY KEY,
                    custumer_number VARCHAR(30) UNIQUE NOT NULL,
                    customer_type   VARCHAR(20) NOT NULL,
                    legal_name      VARCHAR(200) NOT NULL,
                    display_name    VARCHAR(200),
                    tax_id          VARCHAR(50),
                    status          VARCHAR(30) NOT NULL DEFAULT 'Active',
                    assigned_user_id BIGINT,
                    phone           VARCHAR(50),
                    email           VARCHAR(200),
                    website         VARCHAR(300),
                    notes           TEXT,
                    parent_name     VARCHAR(200),
                    do_folder_path  VARCHAR(300),
                    do_storage_status VARCHAR(50),
                    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                ALTER TABLE customer ADD COLUMN IF NOT EXISTS parent_name VARCHAR(200);
                ALTER TABLE customer ADD COLUMN IF NOT EXISTS do_folder_path VARCHAR(300);
                ALTER TABLE customer ADD COLUMN IF NOT EXISTS do_storage_status VARCHAR(50);
                UPDATE customer SET parent_name = 'VRT Services' WHERE parent_name IS NULL OR parent_name = '';

                CREATE TABLE IF NOT EXISTS "ParentClientMap" (
                    "id"          VARCHAR(100) PRIMARY KEY,
                    "parentName"  VARCHAR(200) NOT NULL,
                    "clientName"  VARCHAR(200) NOT NULL,
                    "createdAt"   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updatedAt"   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE UNIQUE INDEX IF NOT EXISTS "ParentClientMap_parentName_clientName_key" ON "ParentClientMap" ("parentName", "clientName");
            """)

            # Backfill ParentClientMap for existing customer records
            try:
                cur.execute("SELECT parent_name, legal_name, display_name FROM customer WHERE parent_name IS NOT NULL AND parent_name != '';")
                customers_to_map = cur.fetchall() or []
                for p_name, l_name, d_name in customers_to_map:
                    sync_customer_parent_mapping(cur, p_name, l_name, d_name)
            except Exception as backfill_err:
                print(f"Warning: Backfill parent-client mappings failed: {backfill_err}")

            conn.commit()
            print("Customer table initialized successfully.")
    except Exception as e:
        print(f"Error initializing customer table: {e}")
    finally:
        if conn:
            conn.close()

def init_checklist_table():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer_task_checklist (
                    id                                 BIGSERIAL PRIMARY KEY,
                    customer_id                        BIGINT REFERENCES customer(id) ON DELETE CASCADE,
                    period                             VARCHAR(20) NOT NULL,
                    bank_statement_received            BOOLEAN NOT NULL DEFAULT FALSE,
                    check_images_received              BOOLEAN NOT NULL DEFAULT FALSE,
                    extraction_ai_categorization_done  BOOLEAN NOT NULL DEFAULT FALSE,
                    accountant_reviewed               BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_docs_requested                 BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_docs_received                  BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_organizer                      BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_preparation                    BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_review                         BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_client_signature               BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_efile                          BOOLEAN NOT NULL DEFAULT FALSE,
                    tax_accepted                       BOOLEAN NOT NULL DEFAULT FALSE,
                    notes                              TEXT,
                    tax_notes                          TEXT,
                    created_at                         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at                         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, period)
                );
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_docs_requested BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_docs_received BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_organizer BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_preparation BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_review BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_client_signature BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_efile BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_accepted BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE customer_task_checklist ADD COLUMN IF NOT EXISTS tax_notes TEXT;
            """)
            conn.commit()
            print("Customer task checklist table initialized successfully.")
    except Exception as e:
        print(f"Error initializing customer task checklist table: {e}")
    finally:
        if conn:
            conn.close()

def init_communications_table():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer_communications (
                    id                BIGSERIAL PRIMARY KEY,
                    customer_id       BIGINT REFERENCES customer(id) ON DELETE CASCADE,
                    direction         VARCHAR(10) NOT NULL,
                    sender_email      VARCHAR(200) NOT NULL,
                    recipient_email   VARCHAR(200) NOT NULL,
                    reply_to_email    VARCHAR(200),
                    subject           VARCHAR(300),
                    body_text         TEXT,
                    attachments_json  JSONB DEFAULT '[]'::jsonb,
                    status            VARCHAR(20) DEFAULT 'DELIVERED',
                    is_read           BOOLEAN DEFAULT FALSE,
                    read_at           TIMESTAMP,
                    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                ALTER TABLE customer_communications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;
                ALTER TABLE customer_communications ADD COLUMN IF NOT EXISTS read_at TIMESTAMP;
            """)
            conn.commit()
            print("Customer communications table initialized successfully.")
    except Exception as e:
        print(f"Error initializing customer communications table: {e}")
    finally:
        if conn:
            conn.close()

def init_webhook_debug_table():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS webhook_debug_log (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payload_json TEXT,
                    sender_email TEXT,
                    recipient_email TEXT,
                    subject TEXT,
                    body_text TEXT,
                    customer_id INT,
                    status TEXT
                );
            """)
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing webhook_debug_log table: {e}")

def cleanup_duplicate_communications():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM customer_communications 
                WHERE subject ILIKE '📩 New Reply Received%' OR sender_email ILIKE 'notification@datalazo.net';
            """)
            cur.execute("""
                DELETE FROM customer_communications c1
                USING customer_communications c2
                WHERE c1.id > c2.id 
                  AND c1.customer_id = c2.customer_id 
                  AND c1.direction = 'INBOUND' 
                  AND c2.direction = 'INBOUND'
                  AND c1.subject = c2.subject
                  AND (c1.created_at - c2.created_at) < INTERVAL '5 minutes';
            """)
            conn.commit()
        conn.close()
        print("Cleaned up duplicate communication logs successfully.")
    except Exception as e:
        print(f"Error cleaning up communications: {e}")

def init_history_table():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "ClientTransactionHistory" (
                    "id"              VARCHAR(100) PRIMARY KEY,
                    "clientName"      VARCHAR(255) NOT NULL,
                    "parentName"      VARCHAR(255),
                    "pattern"         VARCHAR(255) NOT NULL,
                    "description"     TEXT,
                    "accountNumber"   VARCHAR(100) NOT NULL,
                    "accountName"     VARCHAR(255),
                    "transactionType" VARCHAR(50) DEFAULT 'ALL',
                    "source"          VARCHAR(50) DEFAULT 'MANUAL',
                    "useCount"        INT DEFAULT 1,
                    "createdAt"       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    "updatedAt"       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                ALTER TABLE "ClientTransactionHistory" ADD COLUMN IF NOT EXISTS "description" TEXT;
                ALTER TABLE "ClientTransactionHistory" ADD COLUMN IF NOT EXISTS "confidenceScore" DOUBLE PRECISION DEFAULT 1.0;
                ALTER TABLE "ClientTransactionHistory" ALTER COLUMN "confidenceScore" SET DEFAULT 1.0;
                ALTER TABLE "ClientTransactionHistory" ALTER COLUMN "confidenceScore" DROP NOT NULL;

                DELETE FROM "ClientTransactionHistory" a USING "ClientTransactionHistory" b
                WHERE a.ctid < b.ctid 
                  AND a."clientName" = b."clientName" 
                  AND a."pattern" = b."pattern" 
                  AND a."transactionType" = b."transactionType";

                CREATE UNIQUE INDEX IF NOT EXISTS "uniq_client_pattern_txtype_idx" 
                ON "ClientTransactionHistory" ("clientName", "pattern", "transactionType");
            """)
            conn.commit()
        conn.close()
        print("ClientTransactionHistory table initialized successfully.")
    except Exception as e:
        print(f"Error initializing ClientTransactionHistory table: {e}")

def init_coa_table():
    """Ensure ClientChartOfAccounts table exists with a UNIQUE index on (clientName, accountNumber)."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "ClientChartOfAccounts" (
                    "id"            VARCHAR(100) PRIMARY KEY,
                    "clientName"    VARCHAR(200) NOT NULL,
                    "parentName"    VARCHAR(200),
                    "accountNumber" VARCHAR(50) NOT NULL,
                    "accountName"   VARCHAR(200) NOT NULL,
                    "type"          VARCHAR(50),
                    "subType"       VARCHAR(100),
                    "level"         INT DEFAULT 0,
                    "createdAt"     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updatedAt"     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                -- Deduplicate any existing duplicates before creating unique index
                DELETE FROM "ClientChartOfAccounts" a USING "ClientChartOfAccounts" b
                WHERE a."id" < b."id" 
                  AND a."clientName" = b."clientName" 
                  AND a."accountNumber" = b."accountNumber";

                CREATE UNIQUE INDEX IF NOT EXISTS "ClientChartOfAccounts_clientName_accountNumber_key" 
                ON "ClientChartOfAccounts" ("clientName", "accountNumber");
            """)
            conn.commit()
        print("ClientChartOfAccounts table initialized successfully.")
    except Exception as e:
        print(f"Error initializing ClientChartOfAccounts table: {e}")
def ensure_catchall_customer():
    """Ensure system catch-all customer (CUST-0000) exists for routing unassigned inbound emails."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO customer (
                    custumer_number, customer_type, legal_name, display_name,
                    status, parent_name, created_at, updated_at
                ) VALUES (
                    'CUST-0000', 'System', 'Unassigned Inbound Emails', 'Unassigned / General Inbox',
                    'Active', 'VRT Services', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (custumer_number) DO NOTHING;
            """)
            conn.commit()
    except Exception as e:
        print(f"Notice ensuring catch-all customer CUST-0000: {e}")
    finally:
        if conn:
            conn.close()

try:
    init_customer_table()
    ensure_catchall_customer()
    init_checklist_table()
    init_communications_table()
    init_webhook_debug_table()
    init_history_table()
    init_coa_table()
    cleanup_duplicate_communications()
except Exception as e:
    print(f"Startup table init exception: {e}")

def extract_period_from_key(key_str: str) -> str:
    """
    Extracts YYYY-MM period from S3 key or folder path.
    Recognizes:
    - '2026/April' or '2026/Apr' or 'Year 2026/Apr' -> '2026-04'
    - '2026-04' or '2026_04' or '2026/04' -> '2026-04'
    - 'April 2026' or 'Apr 2026' -> '2026-04'
    """
    if not key_str:
        import datetime
        return datetime.datetime.now().strftime("%Y-%m")

    import re
    months_map = {
        "jan": "01", "january": "01",
        "feb": "02", "february": "02",
        "mar": "03", "march": "03",
        "apr": "04", "april": "04",
        "may": "05",
        "jun": "06", "june": "06",
        "jul": "07", "july": "07",
        "aug": "08", "august": "08",
        "sep": "09", "september": "09", "sept": "09",
        "oct": "10", "october": "10",
        "nov": "11", "november": "11",
        "dec": "12", "december": "12"
    }

    clean = key_str.replace("\\", "/")

    # 1. Match YYYY-MM or YYYY_MM or YYYY/MM (e.g. 2026-07 or 2026/07)
    m = re.search(r'\b(20\d{2})[\/\-_](0[1-9]|1[0-2])\b', clean)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # 2. Match YYYY/MonthName or Year YYYY/MonthName (e.g. 2026/April, Year 2026/Apr)
    m = re.search(r'\b(?:Year\s*)?(20\d{2})[\/\-_\s]+([a-zA-Z]{3,9})\b', clean, re.IGNORECASE)
    if m:
        year = m.group(1)
        month_str = m.group(2).lower()
        if month_str in months_map:
            return f"{year}-{months_map[month_str]}"

    # 3. Match MonthName YYYY (e.g. April 2026, Jul 2026)
    m = re.search(r'\b([a-zA-Z]{3,9})[\/\-_\s]+(20\d{2})\b', clean, re.IGNORECASE)
    if m:
        month_str = m.group(1).lower()
        year = m.group(2)
        if month_str in months_map:
            return f"{year}-{months_map[month_str]}"

    import datetime
    return datetime.datetime.now().strftime("%Y-%m")

def update_customer_checklist_milestone(customer_id: int, period: str | None, milestone: str):
    if not customer_id:
        return
    import datetime
    if not period or not period.strip():
        period = datetime.datetime.now().strftime("%Y-%m")

    col_map = {
        "statement_received": "bank_statement_received",
        "checks_received": "check_images_received",
        "extraction_done": "extraction_ai_categorization_done",
        "accountant_reviewed": "accountant_reviewed",
        "tax_docs_requested": "tax_docs_requested",
        "tax_docs_received": "tax_docs_received",
        "tax_organizer": "tax_organizer",
        "tax_preparation": "tax_preparation",
        "tax_review": "tax_review",
        "tax_client_signature": "tax_client_signature",
        "tax_efile": "tax_efile",
        "tax_accepted": "tax_accepted"
    }

    target_col = col_map.get(milestone)
    if not target_col:
        return

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO customer_task_checklist (customer_id, period, {target_col}, updated_at)
                VALUES (%s, %s, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (customer_id, period)
                DO UPDATE SET {target_col} = TRUE, updated_at = CURRENT_TIMESTAMP;
            """, (customer_id, period))
            conn.commit()
    except Exception as e:
        print(f"Error updating checklist milestone '{milestone}' for customer {customer_id}: {e}")
    finally:
        if conn:
            conn.close()

# ── DigitalOcean Spaces Config & Storage Helpers ────────────────────────────────
DO_SPACES_KEY      = os.environ.get("DO_SPACES_KEY", "")
DO_SPACES_SECRET   = os.environ.get("DO_SPACES_SECRET", "")
DO_SPACES_ENDPOINT = os.environ.get("DO_SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
DO_SPACES_BUCKET   = os.environ.get("DO_SPACES_BUCKET", "datalazocrm")
DO_SPACES_REGION   = os.environ.get("DO_SPACES_REGION", "nyc3")

def get_s3_client():
    key = os.environ.get("DO_SPACES_KEY") or DO_SPACES_KEY
    secret = os.environ.get("DO_SPACES_SECRET") or DO_SPACES_SECRET
    endpoint = os.environ.get("DO_SPACES_ENDPOINT") or DO_SPACES_ENDPOINT
    region = os.environ.get("DO_SPACES_REGION") or DO_SPACES_REGION

    if not secret:
        print("[DO SPACES] Warning: DO_SPACES_SECRET is empty. Please set environment variable DO_SPACES_SECRET.")
        return None, "DO_SPACES_SECRET environment variable is missing"

    try:
        import boto3
        session = boto3.session.Session()
        client = session.client(
            's3',
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret
        )
        return client, None
    except Exception as e:
        print(f"[DO SPACES] Error creating boto3 S3 client: {e}")
        return None, str(e)

def sanitize_folder_name(name: str) -> str:
    """Sanitizes customer name for folder path, stripping invalid characters while keeping human readability."""
    if not name:
        return "Unnamed_Customer"
    cleaned = name.strip()
    cleaned = cleaned.replace('/', '-').replace('\\', '-')
    return cleaned

def get_customer_root_folder_path(cust: dict) -> str:
    """Returns stored do_folder_path or fallback path including parent_name if present."""
    if not cust:
        return ""
    p_name = (cust.get("parent_name") or "").strip()
    c_name = (cust.get("legal_name") or "").strip()
    stored_path = (cust.get("do_folder_path") or "").strip()

    if stored_path:
        if not stored_path.endswith('/'):
            stored_path += '/'
        if p_name and not stored_path.lower().startswith(f"{sanitize_folder_name(p_name).lower()}/"):
            stored_path = f"{sanitize_folder_name(p_name)}/{stored_path}"
        return stored_path

    if p_name:
        return f"{sanitize_folder_name(p_name)}/{sanitize_folder_name(c_name)}/"
    return f"{sanitize_folder_name(c_name)}/"

def init_customer_do_folders(customer_id: int, legal_name: str, year: int = None, parent_name: str = None, customer_type: str = None) -> tuple[bool, str, list[str]]:
    """
    Creates folder structure in DigitalOcean Spaces for a customer:
    If customer_type is 'Individual':
      <Parent Name>/<Customer Name>/
        Tax Documents/
          Tax Year <YYYY>/
          Tax Year <YYYY-1>/
    If customer_type is 'Business' (default):
      <Parent Name>/<Customer Name>/
        Bank Statements/
          Year <YYYY>/
        Check Images/
          Year <YYYY>/
            Jan/ ... Dec/
        Tax Documents/
          Tax Year <YYYY>/
    Returns (success, root_folder_path, list_of_created_folders).
    """
    import datetime
    if not year:
        year = datetime.datetime.now().year

    if customer_id and (not parent_name or not customer_type):
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT parent_name, customer_type FROM customer WHERE id = %s;", (customer_id,))
                row = cur.fetchone()
                if row:
                    if not parent_name and row[0]: parent_name = row[0]
                    if not customer_type and row[1]: customer_type = row[1]
            conn.close()
        except Exception as ex:
            print(f"Warning: Could not fetch customer info for customer {customer_id}: {ex}")

    clean_name = sanitize_folder_name(legal_name)
    if parent_name and parent_name.strip():
        clean_parent = sanitize_folder_name(parent_name)
        root_path = f"{clean_parent}/{clean_name}/"
    else:
        root_path = f"{clean_name}/"

    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

    is_individual = customer_type and customer_type.strip().lower() == "individual"

    if is_individual:
        folders_to_create = [
            root_path,
            f"{root_path}Inbox/",
            f"{root_path}Tax Documents/",
            f"{root_path}Tax Documents/Tax Year {year}/",
            f"{root_path}Tax Documents/Tax Year {year - 1}/",
        ]
    else:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        folders_to_create = [
            root_path,
            f"{root_path}Inbox/",
            f"{root_path}Bank Statements/",
            f"{root_path}Bank Statements/Year {year}/",
            f"{root_path}Check Images/",
            f"{root_path}Check Images/Year {year}/",
            f"{root_path}Tax Documents/",
            f"{root_path}Tax Documents/Tax Year {year}/",
        ]
        for m in months:
            folders_to_create.append(f"{root_path}Check Images/Year {year}/{m}/")

    client, err_msg = get_s3_client()

    if not client:
        update_customer_storage_status(customer_id, root_path, "Pending Secret Key")
        return False, root_path, [f"Notice: {err_msg}"]

    created_folders = []
    try:
        for folder_key in folders_to_create:
            client.put_object(
                Bucket=bucket,
                Key=folder_key,
                Body=b'',
                ACL='private'
            )
            created_folders.append(folder_key)

        update_customer_storage_status(customer_id, root_path, "Initialized")
        print(f"[DO SPACES] Successfully initialized {len(created_folders)} folders for '{legal_name}' (Parent: '{parent_name}') in bucket '{bucket}'")
        return True, root_path, created_folders
    except Exception as e:
        error_detail = str(e)
        print(f"[DO SPACES] Failed to create folders for '{legal_name}': {error_detail}")
        update_customer_storage_status(customer_id, root_path, f"Error: {error_detail}")
        return False, root_path, [f"Error: {error_detail}"]

def update_customer_storage_status(customer_id: int, folder_path: str, status: str):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE customer SET
                    do_folder_path = %s,
                    do_storage_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (folder_path, status, customer_id))
            conn.commit()
    except Exception as e:
        print(f"Error updating customer storage status in DB: {e}")
    finally:
        if conn:
            conn.close()

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        parts = stored_hash.split(':')
        if len(parts) != 2:
            return False
        salt, key_hex = parts
        hashed_bytes = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt.encode('utf-8'),
            n=16384,
            r=8,
            p=1,
            dklen=64
        )
        key_bytes = bytes.fromhex(key_hex)
        return hmac.compare_digest(hashed_bytes, key_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_client_user(username: str) -> dict | None:
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM "ClientUser" WHERE username = %s;', (username,))
            user = cur.fetchone()
            if not user:
                return None
            
            # Check if monthly usage needs to be reset for a new month
            last_updated = user.get("updatedAt")
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            
            is_new_month = False
            months_diff = 0
            if last_updated:
                now_compare = now.replace(tzinfo=None) if last_updated.tzinfo is None else now
                months_diff = (now_compare.year - last_updated.year) * 12 + (now_compare.month - last_updated.month)
                if months_diff > 0:
                    is_new_month = True
            else:
                is_new_month = True
                months_diff = 1
                
            if is_new_month:
                actual = user.get("monthlyUsageActual", 0) or 0
                new_prev = actual if months_diff == 1 else 0
                new_actual = 0
                cur.execute(
                    'UPDATE "ClientUser" SET "monthlyUsageActual" = %s, "monthlyUsagePrevious" = %s, "updatedAt" = %s WHERE id = %s;',
                    (new_actual, new_prev, now, user["id"])
                )
                conn.commit()
                user["monthlyUsageActual"] = new_actual
                user["monthlyUsagePrevious"] = new_prev
                user["updatedAt"] = now
                print(f"[USAGE AUTO-RESET] User '{username}' logged in/queried in new month (gap: {months_diff}m). Reset actual to 0, previous to {new_prev}.")

            return user
    except Exception as e:
        print(f"Database error fetching user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def normalize_parent_name(parent_name: str | None) -> str:
    """Normalizes parent company name, defaulting to VRT Services if empty."""
    if not parent_name:
        return "VRT Services"
    return str(parent_name).strip()

def get_user_parent_name(username: str) -> str:
    """Fetch the parent company name for a given user from their Client account, defaulting to VRT Services."""
    user = get_client_user(username)
    if not user:
        return "VRT Services"
    client_id = user.get("clientId")
    if not client_id:
        return "VRT Services"
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT company, name FROM "Client" WHERE id = %s;', (client_id,))
            client = cur.fetchone()
            if client:
                parent = (client.get("company") or client.get("name") or "").strip()
                return normalize_parent_name(parent)
    except Exception as e:
        print(f"Database error fetching client parent name: {e}")
    finally:
        if conn:
            conn.close()
    return "VRT Services"

def get_client_coa(client_name: str, parent_name: str = None) -> list[dict]:
    """Fetch Chart of Accounts list for a client from ClientChartOfAccounts table filtering by clientName and parentName."""
    parent_name = normalize_parent_name(parent_name)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT "accountNumber", "accountName", "type", "subType", "level", "parentName"
                FROM "ClientChartOfAccounts"
                WHERE (LOWER("clientName") = LOWER(%s) OR "clientName" = 'DEFAULT')
                  AND (LOWER("parentName") = LOWER(%s) OR "parentName" IS NULL OR "parentName" = '' OR "parentName" = 'VRT Services')
                ORDER BY "accountNumber" ASC;
            ''', (client_name, parent_name))
            records = cur.fetchall() or []
            if records:
                return records

            # Fallback query matching clientName only if no records found with parentName filter
            cur.execute('''
                SELECT "accountNumber", "accountName", "type", "subType", "level", "parentName"
                FROM "ClientChartOfAccounts"
                WHERE LOWER("clientName") = LOWER(%s) OR "clientName" = 'DEFAULT'
                ORDER BY "accountNumber" ASC;
            ''', (client_name,))
            return cur.fetchall() or []
    except Exception as e:
        print(f"Database error fetching COA for {client_name} (Parent: {parent_name}): {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_client_history_rules(client_name: str, parent_name: str = None) -> list[dict]:
    """Fetch learned vendor matching rules from ClientTransactionHistory table with fallbacks for parentName."""
    parent_name = normalize_parent_name(parent_name)
    conn = None
    rules = []
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if client_name:
                cur.execute('''
                    SELECT "pattern", "description", "accountNumber", "accountName", "transactionType", "useCount", "parentName"
                    FROM "ClientTransactionHistory"
                    WHERE (LOWER("clientName") = LOWER(%s) OR "clientName" = 'DEFAULT')
                      AND (LOWER("parentName") = LOWER(%s) OR "parentName" IS NULL OR "parentName" = '' OR "parentName" = 'VRT Services')
                    ORDER BY "useCount" DESC;
                ''', (client_name, parent_name))
                rules = cur.fetchall() or []
            
            if not rules and client_name:
                cur.execute('''
                    SELECT "pattern", "description", "accountNumber", "accountName", "transactionType", "useCount", "parentName"
                    FROM "ClientTransactionHistory"
                    WHERE LOWER("clientName") = LOWER(%s) OR "clientName" = 'DEFAULT'
                    ORDER BY "useCount" DESC;
                ''', (client_name,))
                rules = cur.fetchall() or []

            if not rules:
                cur.execute('''
                    SELECT "pattern", "description", "accountNumber", "accountName", "transactionType", "useCount", "parentName"
                    FROM "ClientTransactionHistory"
                    ORDER BY "useCount" DESC;
                ''')
                rules = cur.fetchall() or []
    except Exception as e:
        print(f"Database error fetching history rules for {client_name} (Parent: {parent_name}): {e}")
    finally:
        if conn:
            conn.close()

    if not rules:
        try:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toirak_mapped_rules.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                print(f"--> Loaded {len(rules)} fallback rules from toirak_mapped_rules.json")
        except Exception as ex:
            print(f"Error loading toirak_mapped_rules.json: {ex}")

    return rules

def save_history_rule(client_name: str, pattern: str, account_number: str, account_name: str = "", tx_type: str = "ALL", parent_name: str = None, description: str = "") -> bool:
    """Save or update a learned vendor rule in ClientTransactionHistory table."""
    parent_name = normalize_parent_name(parent_name)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                SELECT "id" FROM "ClientTransactionHistory"
                WHERE "clientName" = %s AND "pattern" = %s AND "transactionType" = %s;
            ''', (client_name, pattern.upper().strip(), tx_type))
            row = cur.fetchone()
            if row:
                cur.execute('''
                    UPDATE "ClientTransactionHistory"
                    SET "parentName" = %s,
                        "description" = %s,
                        "accountNumber" = %s,
                        "accountName" = %s,
                        "useCount" = "useCount" + 1,
                        "updatedAt" = CURRENT_TIMESTAMP
                    WHERE "id" = %s;
                ''', (parent_name, description.strip(), account_number.strip(), account_name.strip(), row[0]))
            else:
                import uuid
                new_id = str(uuid.uuid4())
                cur.execute('''
                    INSERT INTO "ClientTransactionHistory" ("id", "clientName", "parentName", "pattern", "description", "accountNumber", "accountName", "transactionType", "source", "confidenceScore", "useCount")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'USER_EDIT', 1.0, 1);
                ''', (new_id, client_name, parent_name, pattern.upper().strip(), description.strip(), account_number.strip(), account_name.strip(), tx_type))
            conn.commit()
            return True
    except Exception as e:
        print(f"Database error saving history rule: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_terms_accepted(username: str, ip: str, user_agent: str) -> bool:
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor() as cur:
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            cur.execute(
                'UPDATE "ClientUser" SET "termsAccepted" = True, "termsAcceptedAt" = %s, "termsAcceptedIp" = %s, "termsAcceptedUserAgent" = %s WHERE username = %s;',
                (now, ip, user_agent, username)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Database error updating terms: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_assigned_subdomain(username: str) -> str | None:
    user = get_client_user(username)
    if not user:
        return None
    
    client_id = user.get("clientId")
    if not client_id:
        return None
        
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT subdomain FROM "Client" WHERE id = %s;', (client_id,))
            client = cur.fetchone()
            if client and client.get("subdomain"):
                return client.get("subdomain").strip()
    except Exception as e:
        print(f"Database error fetching client subdomain: {e}")
    finally:
        if conn:
            conn.close()
            
    return None

def get_client_subdomain(username: str) -> str:
    subdomain = get_user_assigned_subdomain(username)
    return subdomain if subdomain else "vrt.datalazo.net"

def record_user_usage(username: str, page_count: int):
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT "monthlyUsageActual", "monthlyUsagePrevious", "updatedAt" FROM "ClientUser" WHERE username = %s;', (username,))
            user = cur.fetchone()
            if not user:
                return
            
            actual = user.get("monthlyUsageActual", 0) or 0
            prev = user.get("monthlyUsagePrevious", 0) or 0
            last_updated = user.get("updatedAt")
            
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Determine if a new month has started and calculate month gap
            is_new_month = False
            months_diff = 0
            if last_updated:
                # Remove timezone for database timestamps without time zone
                if last_updated.tzinfo is None:
                    now_compare = now.replace(tzinfo=None)
                else:
                    now_compare = now
                
                months_diff = (now_compare.year - last_updated.year) * 12 + (now_compare.month - last_updated.month)
                if months_diff > 0:
                    is_new_month = True
            else:
                is_new_month = True
                months_diff = 1
                
            if is_new_month:
                # If gap is exactly 1 month, move actual -> previous.
                # If gap is > 1 month (e.g. inactive for a full calendar month), previous month had 0 usage.
                new_prev = actual if months_diff == 1 else 0
                new_actual = page_count
            else:
                new_prev = prev
                new_actual = actual + page_count
                
            cur.execute(
                'UPDATE "ClientUser" SET "monthlyUsageActual" = %s, "monthlyUsagePrevious" = %s, "updatedAt" = %s WHERE username = %s;',
                (new_actual, new_prev, now, username)
            )
            conn.commit()
            print(f"Recorded usage for {username}: {page_count} pages. Actual: {new_actual}, Previous: {new_prev}")
    except Exception as e:
        print(f"Database error recording usage: {e}")
    finally:
        if conn:
            conn.close()

def record_login(username: str, site: str, ip: str, user_agent: str):
    conn = None
    try:
        conn = get_db_connection("datalazo")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'INSERT INTO "LoginLog" (username, site, "ipAddress", "userAgent") VALUES (%s, %s, %s, %s);',
                (username, site, ip, user_agent)
            )
            conn.commit()
            print(f"Recorded login log for {username} from {ip} on site {site}")
    except Exception as e:
        print(f"Database error recording login: {e}")
    finally:
        if conn:
            conn.close()

# ── QuickBooks Online (QBO) OAuth & API Integration ───────────────────────────
QBO_CLIENT_ID     = os.environ.get("QBO_CLIENT_ID", "")
QBO_CLIENT_SECRET = os.environ.get("QBO_CLIENT_SECRET", "")
QBO_REDIRECT_URI  = os.environ.get("QBO_REDIRECT_URI", "https://datalazo.net/auth/qbo/callback")
QBO_ENVIRONMENT   = os.environ.get("QBO_ENVIRONMENT", "sandbox").lower()

QBO_AUTH_URL      = "https://appcenter.intuit.com/connect/oauth2"
QBO_TOKEN_URL     = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

def get_qbo_api_base_url(realm_id: str) -> str:
    if QBO_ENVIRONMENT == "production":
        return f"https://quickbooks.api.intuit.com/v3/company/{realm_id}"
    else:
        return f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}"

def init_qbo_db():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS "QboConnection" (
                    "id" SERIAL PRIMARY KEY,
                    "clientId" TEXT UNIQUE NOT NULL,
                    "realmId" TEXT NOT NULL,
                    "accessToken" TEXT NOT NULL,
                    "refreshToken" TEXT NOT NULL,
                    "accessTokenExpiresAt" TIMESTAMP WITH TIME ZONE,
                    "refreshTokenExpiresAt" TIMESTAMP WITH TIME ZONE,
                    "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()
    except Exception as e:
        print(f"Error initializing QboConnection table: {e}")
    finally:
        if conn:
            conn.close()

    try:
        conn_dlz = get_db_connection("datalazo")
        with conn_dlz.cursor() as cur:
            cur.execute('ALTER TABLE "ClientUser" ADD COLUMN IF NOT EXISTS "sessionToken" TEXT;')
            conn_dlz.commit()
        conn_dlz.close()
    except Exception as e_col:
        print(f"sessionToken column check: {e_col}")

init_qbo_db()

def save_qbo_connection(client_id_key: str, realm_id: str, access_token: str, refresh_token: str, expires_in: int, refresh_expires_in: int = 8726400):
    conn = None
    try:
        conn = get_db_connection()
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        access_expires_at = now + datetime.timedelta(seconds=expires_in)
        refresh_expires_at = now + datetime.timedelta(seconds=refresh_expires_in)
        
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO "QboConnection" ("clientId", "realmId", "accessToken", "refreshToken", "accessTokenExpiresAt", "refreshTokenExpiresAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("clientId") DO UPDATE SET
                    "realmId" = EXCLUDED."realmId",
                    "accessToken" = EXCLUDED."accessToken",
                    "refreshToken" = EXCLUDED."refreshToken",
                    "accessTokenExpiresAt" = EXCLUDED."accessTokenExpiresAt",
                    "refreshTokenExpiresAt" = EXCLUDED."refreshTokenExpiresAt",
                    "updatedAt" = EXCLUDED."updatedAt";
            ''', (client_id_key, realm_id, access_token, refresh_token, access_expires_at, refresh_expires_at, now))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving QboConnection: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_qbo_connection(client_id_key: str) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM "QboConnection" WHERE "clientId" = %s;', (client_id_key,))
            return cur.fetchone()
    except Exception as e:
        print(f"Error fetching QboConnection: {e}")
        return None
    finally:
        if conn:
            conn.close()

def refresh_qbo_tokens(refresh_token: str) -> dict | None:
    if not QBO_CLIENT_ID or not QBO_CLIENT_SECRET:
        return None

    import urllib.parse
    auth_header = base64.b64encode(f"{QBO_CLIENT_ID}:{QBO_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }).encode("utf-8")

    req = urllib.request.Request(QBO_TOKEN_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"Error refreshing QBO token: {e}")
        return None

def get_valid_qbo_access_token(client_id_key: str) -> tuple[str | None, str | None]:
    try:
        qbo_conn = get_qbo_connection(client_id_key)
        if not qbo_conn:
            return None, None

        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        access_expires_at = qbo_conn.get("accessTokenExpiresAt")
        
        if access_expires_at:
            if isinstance(access_expires_at, str):
                try:
                    access_expires_at = datetime.datetime.fromisoformat(access_expires_at.replace('Z', '+00:00'))
                except Exception:
                    access_expires_at = None

            if access_expires_at and isinstance(access_expires_at, datetime.datetime):
                if access_expires_at.tzinfo is None:
                    now_compare = now.replace(tzinfo=None)
                else:
                    now_compare = now
                    
                if access_expires_at <= (now_compare + datetime.timedelta(minutes=5)):
                    res = refresh_qbo_tokens(qbo_conn.get("refreshToken", ""))
                    if res and "access_token" in res:
                        new_access_token = res["access_token"]
                        new_refresh_token = res.get("refresh_token", qbo_conn.get("refreshToken"))
                        expires_in = res.get("expires_in", 3600)
                        refresh_expires_in = res.get("x_refresh_token_expires_in", 8726400)
                        save_qbo_connection(client_id_key, qbo_conn.get("realmId"), new_access_token, new_refresh_token, expires_in, refresh_expires_in)
                        return new_access_token, qbo_conn.get("realmId")
                    else:
                        return None, None

        return qbo_conn.get("accessToken"), qbo_conn.get("realmId")
    except Exception as e:
        print(f"Error checking QBO access token: {e}")
        return None, None

def fetch_qbo_chart_of_accounts(access_token: str, realm_id: str) -> list[dict]:
    import urllib.parse
    base_url = get_qbo_api_base_url(realm_id)
    query = "SELECT * FROM Account MAXRESULTS 1000"
    url = f"{base_url}/query?query={urllib.parse.quote(query)}&minorversion=65"
    
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            query_response = data.get("QueryResponse", {})
            return query_response.get("Account", [])
    except Exception as e:
        print(f"Error fetching QBO Chart of Accounts: {e}")
        return []

def resolve_qbo_account_ids(access_token: str, realm_id: str, debit_num="260", credit_num="500") -> tuple[dict | None, dict | None]:
    accounts = fetch_qbo_chart_of_accounts(access_token, realm_id)
    
    debit_acc = None
    credit_acc = None
    
    for acc in accounts:
        acct_num = str(acc.get("AcctNum", "")).strip()
        name = str(acc.get("Name", "")).strip()
        
        if not debit_acc and (acct_num == str(debit_num) or name == str(debit_num)):
            debit_acc = acc
        if not credit_acc and (acct_num == str(credit_num) or name == str(credit_num)):
            credit_acc = acc
            
    if not debit_acc:
        for acc in accounts:
            if acc.get("AccountType") in ("Bank", "Other Current Asset"):
                debit_acc = acc
                break
    if not credit_acc:
        for acc in accounts:
            if acc.get("AccountType") in ("Expense", "Cost of Goods Sold", "Other Expense"):
                credit_acc = acc
                break

    if not debit_acc and accounts:
        debit_acc = accounts[0]
    if not credit_acc and len(accounts) > 1:
        credit_acc = accounts[1]
    elif not credit_acc and accounts:
        credit_acc = accounts[0]

    return debit_acc, credit_acc

def fetch_qbo_company_name(access_token: str, realm_id: str) -> str:
    base_url = get_qbo_api_base_url(realm_id)
    url = f"{base_url}/companyinfo/{realm_id}?minorversion=65"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cinfo = data.get("CompanyInfo", {})
            return cinfo.get("CompanyName", "") or ""
    except Exception as e:
        print(f"Error fetching QBO company name: {e}")
        return ""


# ── Auth routes ────────────────────────────────────────────────────────────────
@app.get("/api/check-terms")
async def check_terms(username: str = ""):
    username_clean = username.strip()
    if not username_clean:
        return {"termsAccepted": False}
    user = get_client_user(username_clean)
    if user:
        return {"termsAccepted": bool(user.get("termsAccepted", False))}
    return {"termsAccepted": False}

@app.get("/api/session-status")
async def check_session_status(request: Request):
    token, username, reason = get_current_session_info(request)
    if not username:
        return {"valid": False, "reason": reason or "Session invalid."}
    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        return {"valid": False, "reason": f"Access denied: Your account is assigned to '{assigned_site}'."}
    return {"valid": True, "username": username}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = "", username: str = ""):
    # Already logged in → check if allowed on current site
    current_username = get_current_username(request)
    if current_username:
        allowed, _ = is_user_allowed_on_site(current_username, request)
        if allowed:
            return RedirectResponse("/dashboard", status_code=302)
        else:
            token = request.cookies.get(COOKIE_NAME)
            if token:
                valid_sessions.pop(token, None)
    
    terms_accepted = False
    if username:
        user = get_client_user(username.strip())
        if user:
            terms_accepted = bool(user.get("termsAccepted", False))

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error, "username": username, "terms_accepted": terms_accepted}
    )

@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    terms: str = Form(None)
):
    username_clean = username.strip()
    
    # 1. Try database client user authentication first
    user = get_client_user(username_clean)
    if user:
        if verify_password(password, user["password"]):
            # Validate site assignment permission
            allowed, assigned_site = is_user_allowed_on_site(username_clean, request)
            if not allowed:
                request_host = get_request_host(request)
                return templates.TemplateResponse(
                    request=request,
                    name="login.html",
                    context={
                        "error": f"Access denied: Your account is assigned to '{assigned_site}' and cannot log in on '{request_host}'.",
                        "username": username_clean,
                        "terms_accepted": bool(user.get("termsAccepted", False))
                    },
                    status_code=403
                )

            # Check terms and conditions acceptance status
            if not user.get("termsAccepted", False):
                if not terms:
                    return templates.TemplateResponse(
                        request=request,
                        name="login.html",
                        context={
                            "error": "You must accept the Terms and Conditions to proceed.",
                            "username": username_clean,
                            "terms_accepted": False
                        },
                        status_code=400
                    )
                else:
                    client_ip = get_real_client_ip(request)
                    user_agent = request.headers.get("user-agent", "")
                    update_terms_accepted(username_clean, client_ip, user_agent)
            
            # Create single active session and redirect
            token = create_user_session(username_clean)
            
            # Record login log
            client_ip = get_real_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            site_host = get_request_host(request)
            record_login(username_clean, site_host, client_ip, user_agent)
            
            response = RedirectResponse("/dashboard", status_code=302)
            response.set_cookie(
                key=COOKIE_NAME,
                value=token,
                httponly=True,
                samesite="lax",
                max_age=60 * 60 * 8,   # 8 hours
            )
            return response
            
    # 2. Fallback to environment admin account (only if environment credentials are set)
    if APP_USERNAME and APP_PASSWORD and username_clean == APP_USERNAME and password == APP_PASSWORD:
        allowed, assigned_site = is_user_allowed_on_site(username_clean, request)
        if not allowed:
            request_host = get_request_host(request)
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "error": f"Access denied: Your account is assigned to '{assigned_site}' and cannot log in on '{request_host}'.",
                    "username": username_clean,
                    "terms_accepted": True
                },
                status_code=403
            )

        token = create_user_session(username_clean)
        
        # Record login log
        client_ip = get_real_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        site_host = get_request_host(request)
        record_login(username_clean, site_host, client_ip, user_agent)
        
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 8,   # 8 hours
        )
        return response

    # Bad credentials
    terms_accepted = False
    if user:
        terms_accepted = bool(user.get("termsAccepted", False))

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": "Invalid email or password. Please try again.",
            "username": username_clean,
            "terms_accepted": terms_accepted
        },
        status_code=401,
    )

@app.get("/logout")
async def logout(request: Request, reason: str = ""):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        sess = valid_sessions.pop(token, None)
        if sess and isinstance(sess, dict) and "username" in sess:
            username = sess["username"]
            if active_user_tokens.get(username) == token:
                active_user_tokens.pop(username, None)
                
    redirect_url = "/login"
    if reason == "concurrent":
        redirect_url += "?error=Logged+out:+Your+account+was+accessed+from+another+device+or+location."

    response = RedirectResponse(redirect_url, status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response

def get_user_email(username: str) -> str:
    """Fetch the email address for the logged in user or parent client organization."""
    if not username:
        return get_resend_to_email()

    user = get_client_user(username)
    if user:
        if user.get("email") and "@" in str(user.get("email")):
            return str(user["email"]).strip()
        client_id = user.get("clientId")
        if client_id:
            conn = None
            try:
                conn = get_db_connection("datalazo")
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    try:
                        cur.execute('SELECT email FROM "Client" WHERE id = %s;', (client_id,))
                        c = cur.fetchone()
                        if c and c.get("email") and "@" in str(c.get("email")):
                            return str(c["email"]).strip()
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error fetching email for client_id {client_id}: {e}")
            finally:
                if conn:
                    conn.close()

    if "@" in str(username):
        return str(username).strip()

    return get_resend_to_email()

# ── Protected routes ───────────────────────────────────────────────────────────
def prepare_dashboard_context(request: Request) -> dict | RedirectResponse:
    try:
        username = get_current_username(request)
        if not username:
            return RedirectResponse("/login", status_code=302)
            
        allowed, assigned_site = is_user_allowed_on_site(username, request)
        if not allowed:
            token = request.cookies.get(COOKIE_NAME)
            if token:
                valid_sessions.pop(token, None)
            request_host = get_request_host(request)
            response = RedirectResponse(
                f"/login?error=Access+denied:+Your+account+is+assigned+to+'{assigned_site}'.+You+cannot+access+'{request_host}'.",
                status_code=302
            )
            response.delete_cookie(COOKIE_NAME)
            return response

        company_name = None
        software_name = None
        user_email = None

        user = get_client_user(username)
        client_id_key = str(user.get("clientId")) if (user and user.get("clientId")) else username

        if user:
            if user.get("email") and "@" in str(user.get("email")):
                user_email = str(user.get("email")).strip()

        conn_dlz = None
        try:
            conn_dlz = get_db_connection("datalazo")
            with conn_dlz.cursor(cursor_factory=RealDictCursor) as cur_dlz:
                if user and user.get("clientId"):
                    try:
                        cur_dlz.execute('SELECT company, name, email, "software" FROM "Client" WHERE id = %s;', (user["clientId"],))
                        client = cur_dlz.fetchone()
                        if client:
                            company_name = (client.get("company") or client.get("name") or "").strip()
                            software_name = (client.get("software") or client.get("Software") or "").strip()
                            if not user_email and client.get("email") and "@" in str(client.get("email")):
                                user_email = str(client.get("email")).strip()
                    except Exception as e_c:
                        conn_dlz.rollback()

                if not software_name or not company_name:
                    subdomain = get_client_subdomain(username)
                    search_company = company_name or "VRT Services"
                    cur_dlz.execute('SELECT company, "software" FROM "Client" WHERE company ILIKE %s OR subdomain ILIKE %s LIMIT 1;', 
                                    (f"%{search_company.strip()}%", f"%{subdomain.strip()}%"))
                    fallback_client = cur_dlz.fetchone()
                    if fallback_client:
                        if not software_name:
                            software_name = (fallback_client.get("software") or "").strip()
                        if not company_name:
                            company_name = (fallback_client.get("company") or "").strip()
        except Exception as e:
            print(f"Error fetching Client info from datalazo DB: {e}")
        finally:
            if conn_dlz:
                conn_dlz.close()

        if not company_name:
            if APP_USERNAME and username.lower() == APP_USERNAME.lower():
                company_name = "VRT Services"
            else:
                company_name = "Datalazo Partner"

        if not user_email:
            user_email = get_user_email(username)

        subdomain = get_client_subdomain(username)
        software_config = APP_CONFIG.get("software", {})
        clients_config = APP_CONFIG.get("clients", {})

        client_conf = None
        if software_name and isinstance(software_name, str):
            clean_software = software_name.strip()
            client_conf = software_config.get(clean_software)
            if not client_conf:
                for key, val in software_config.items():
                    if key.lower() == clean_software.lower():
                        client_conf = val
                        break

        if not client_conf:
            client_conf = clients_config.get(subdomain) or software_config.get("Default") or clients_config.get("vrt.datalazo.net", {})

        if not client_conf or "csv_mapping" not in client_conf:
            client_conf = {"csv_mapping": DEFAULT_CSV_MAPPING}

        # Check QBO connection status safely
        qbo_token, qbo_realm_id = None, None
        try:
            qbo_token, qbo_realm_id = get_valid_qbo_access_token(client_id_key)
        except Exception as e_qbo:
            print(f"Error checking QBO token in dashboard context: {e_qbo}")

        qbo_connected = bool(qbo_token and qbo_realm_id)
        qbo_company_name = ""
        if qbo_connected:
            try:
                qbo_company_name = fetch_qbo_company_name(qbo_token, qbo_realm_id)
            except Exception as e_qname:
                print(f"Error fetching QBO company name in dashboard context: {e_qname}")

        user_parent_name = get_user_parent_name(username) or company_name or "VRT Services"

        ctx_reply_to = get_resend_reply_to_email()

        created_at_fmt = ""
        if user and user.get("createdAt"):
            ca = user.get("createdAt")
            created_at_fmt = ca.strftime("%b %d, %Y") if hasattr(ca, "strftime") else str(ca)

        client_user_data = {
            "id": (user.get("id") or "") if user else "",
            "username": username,
            "user_email": user_email or username,
            "client_id": (user.get("clientId") or "") if user else "",
            "contact_name": (client.get("name") or "") if ('client' in locals() and client) else "",
            "company": company_name or "VRT Services",
            "parent_name": user_parent_name,
            "subdomain": subdomain,
            "software": software_name or "",
            "monthly_usage_actual": user.get("monthlyUsageActual", 0) if user else 0,
            "monthly_usage_previous": user.get("monthlyUsagePrevious", 0) if user else 0,
            "terms_accepted": bool(user.get("termsAccepted")) if user else False,
            "created_at": created_at_fmt
        }

        return {
            "client_config": client_conf,
            "username": username,
            "user_email": user_email,
            "company_name": company_name or "Datalazo Partner",
            "parent_name": user_parent_name,
            "software_name": software_name or "",
            "qbo_connected": qbo_connected,
            "qbo_realm_id": qbo_realm_id or "",
            "qbo_company_name": qbo_company_name or "",
            "resend_reply_to_email": ctx_reply_to,
            "client_user": client_user_data
        }
    except Exception as e:
        import traceback
        print(f"[ERROR in prepare_dashboard_context]: {e}")
        traceback.print_exc()
        return {
            "client_config": {"csv_mapping": DEFAULT_CSV_MAPPING},
            "username": get_current_username(request) or "user",
            "user_email": "",
            "company_name": "VRT Services",
            "parent_name": "VRT Services",
            "software_name": "",
            "qbo_connected": False,
            "qbo_realm_id": "",
            "qbo_company_name": "",
            "resend_reply_to_email": "vrt@ostooechei.resend.app",
            "error": f"Context notice: {str(e)}"
        }

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/home", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def read_home_page(request: Request):
    username = get_current_username(request)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"username": username}
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, tab: str = "", msg: str = "", error: str = ""):
    try:
        ctx = prepare_dashboard_context(request)
        if isinstance(ctx, RedirectResponse):
            return ctx
        ctx["msg"] = msg
        ctx["error"] = error
        if tab:
            ctx["active_tab"] = tab
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context=ctx
        )
    except Exception as e:
        import traceback
        print(f"[ERROR rendering dashboard]: {e}")
        traceback.print_exc()
        raise e

@app.get("/ocr", response_class=HTMLResponse)
@app.get("/extractor", response_class=HTMLResponse)
async def read_index(request: Request, msg: str = "", error: str = ""):
    ctx = prepare_dashboard_context(request)
    if isinstance(ctx, RedirectResponse):
        return ctx
    ctx["msg"] = msg
    ctx["error"] = error
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=ctx
    )

# ── Customer CRM API Routes ───────────────────────────────────────────────────
@app.get("/customers", response_class=HTMLResponse)
async def read_customers_page(request: Request, msg: str = "", error: str = ""):
    ctx = prepare_dashboard_context(request)
    if isinstance(ctx, RedirectResponse):
        return ctx
    ctx["msg"] = msg
    ctx["error"] = error
    ctx["active_tab"] = "customers"
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=ctx
    )

@app.get("/knowledge", response_class=HTMLResponse)
@app.get("/kb", response_class=HTMLResponse)
async def read_knowledge_page(request: Request, msg: str = "", error: str = ""):
    ctx = prepare_dashboard_context(request)
    if isinstance(ctx, RedirectResponse):
        return ctx
    ctx["msg"] = msg
    ctx["error"] = error
    ctx["active_tab"] = "knowledge"
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=ctx
    )

# ── Public Client Portal API Routes ─────────────────────────────────────────
@app.api_route("/api/portal/verify-customer", methods=["GET", "POST"])
async def portal_verify_customer(request: Request, customer_id: str = "", email: str = ""):
    cid_raw = customer_id.strip()
    email_raw = email.strip().lower()

    if request.method == "POST":
        try:
            body = await request.json()
            if not cid_raw:
                cid_raw = str(body.get("customer_id") or body.get("code") or body.get("id") or "").strip()
            if not email_raw:
                email_raw = str(body.get("email") or "").strip().lower()
        except Exception:
            pass

    if not cid_raw:
        raise HTTPException(status_code=400, detail="Customer ID is required.")
    if not email_raw:
        raise HTTPException(status_code=400, detail="Registered Email Address is required for security verification.")

    clean_num = re.sub(r'[^0-9]', '', cid_raw)
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Dual-verification: Require Customer ID match AND registered email match
            sql_id_clause = "LOWER(custumer_number) = LOWER(%s)"
            params = [cid_raw]
            if clean_num:
                sql_id_clause += " OR id = %s OR custumer_number = %s OR custumer_number ILIKE %s"
                params.extend([int(clean_num), clean_num, f"%{clean_num}%"])

            sql = f"""
                SELECT * FROM customer 
                WHERE ({sql_id_clause})
                  AND LOWER(COALESCE(email, '')) = LOWER(%s)
                ORDER BY id LIMIT 1;
            """
            params.append(email_raw)

            cur.execute(sql, tuple(params))
            cust = cur.fetchone()
            
            if not cust:
                # Check if customer_id exists under a different email to give diagnostic feedback
                sql_check = f"SELECT email FROM customer WHERE ({sql_id_clause}) LIMIT 1;"
                cur.execute(sql_check, tuple(params[:-1]))
                exist_row = cur.fetchone()
                if exist_row:
                    raise HTTPException(
                        status_code=401, 
                        detail="Authentication failed: The email address provided does not match the registered record for this Customer ID."
                    )
                else:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Customer ID '{cid_raw}' not found. Please verify your Customer ID."
                    )

            ref_code = cust.get("custumer_number") or f"CUST-{cust['id']}"
            return {
                "status": "ok",
                "customer": {
                    "id": cust["id"],
                    "legal_name": cust.get("legal_name") or f"Customer #{cust['id']}",
                    "custumer_number": cust.get("custumer_number") or ref_code,
                    "reference_code": ref_code,
                    "email": cust.get("email") or "",
                    "parent_name": cust.get("parent_name") or "VRT Services"
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR in portal_verify_customer]: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


def send_portal_file_upload_notification(cust: dict, filename: str, subfolder: str = "Inbox", file_key: str = ""):
    """Sends email notification to customer's email and logs to customer_communications history table."""
    try:
        recipient_email = parse_clean_email(cust.get("email") or "")
        if not recipient_email:
            print(f"[PORTAL NOTIFY SKIPPED] Customer {cust.get('id')} has no email configured.")
            return False

        parent_name = (cust.get("parent_name") or "VRT Services").strip()
        sender_display_name = f"{parent_name} Portal"
        
        raw_ref = str(cust.get('custumer_number') or cust.get('id')).strip()
        cust_ref = raw_ref if raw_ref.upper().startswith("CUST-") else f"CUST-{raw_ref}"
        ref_tag = f"[Ref: {cust_ref}]"
        
        subject = f"File Uploaded to {subfolder} Folder {ref_tag}"
        
        message_text = (
            f"Hello {cust.get('legal_name') or 'Valued Client'},\n\n"
            f"A new document has been successfully uploaded to your account's '{subfolder}/' folder:\n\n"
            f"• File Name: {filename}\n"
            f"• Destination: {subfolder}/ Folder\n"
            f"• Account Ref: {cust_ref}\n\n"
            f"Thank you for using the {parent_name} Client Portal."
        )

        formatted_html = f"""
        <div style="font-family: 'Plus Jakarta Sans', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; padding: 24px; border: 1px solid #e2e8f0; border-radius: 14px; background: #ffffff;">
            <div style="border-bottom: 2px solid #00f2fe; padding-bottom: 14px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
                <h2 style="color: #0f172a; margin: 0; font-size: 1.2rem;">{parent_name} Client Portal</h2>
                <span style="background: #e0f2fe; color: #0284c7; padding: 4px 10px; border-radius: 8px; font-size: 0.78rem; font-weight: 700;">DOCUMENT RECEIVED</span>
            </div>
            <p style="font-size: 0.95rem; color: #334155; margin-bottom: 16px;">
                Hello <strong>{cust.get('legal_name') or 'Valued Client'}</strong>,
            </p>
            <p style="font-size: 0.92rem; color: #475569; margin-bottom: 20px;">
                A new file has been uploaded to your secure account <strong>{subfolder}/</strong> folder:
            </p>
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; margin-bottom: 24px;">
                <div style="font-size: 0.88rem; color: #1e293b; margin-bottom: 6px;">📄 <strong>File Name:</strong> {filename}</div>
                <div style="font-size: 0.88rem; color: #1e293b; margin-bottom: 6px;">📁 <strong>Target Folder:</strong> {subfolder}/</div>
                <div style="font-size: 0.88rem; color: #1e293b;">🏷️ <strong>Account Ref:</strong> {cust_ref}</div>
            </div>
            <div style="border-top: 1px solid #e2e8f0; padding-top: 14px; font-size: 0.78rem; color: #94a3b8;">
                <p style="margin: 0;">This is an automated notification log from your {parent_name} Client Portal.</p>
                <p style="margin: 4px 0 0 0; font-family: monospace;">Ref: {cust_ref}</p>
            </div>
        </div>
        """

        resend_key = (
            os.environ.get("RESEND_API_KEY") or
            os.environ.get("RESEND_KEY") or
            os.environ.get("RESEND_API_TOKEN") or
            os.environ.get("RESEND_TOKEN")
        )
        if resend_key:
            resend_key = resend_key.strip().strip('\'"')

        clean_from = get_resend_from_email()
        reply_to = get_resend_reply_to_email()

        if resend_key:
            try:
                payload = {
                    "from": format_resend_from_header(sender_display_name),
                    "to": [recipient_email],
                    "reply_to": reply_to,
                    "subject": subject,
                    "html": formatted_html,
                    "text": message_text
                }
                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {resend_key.strip()}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 CRM Portal Notify"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode("utf-8")
                    print(f"[PORTAL EMAIL SENT] {recipient_email}: {res_body}")
            except Exception as mail_err:
                print(f"[WARNING sending email via Resend]: {mail_err}")

        # Log as INBOUND communication record so it triggers notification alert on CRM panel!
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                inbound_subject = f"📎 Client Uploaded Document: {filename} {ref_tag}"
                inbound_body = (
                    f"Client uploaded new file '{filename}' directly to the '{subfolder}/' folder via Client Portal.\n\n"
                    f"• Account: {cust.get('legal_name') or 'Client'} ({cust_ref})\n"
                    f"• File Name: {filename}\n"
                    f"• Destination: {subfolder}/\n"
                    f"• Email: {recipient_email or 'N/A'}"
                )
                att_payload = [{"filename": filename, "file_key": file_key}] if file_key else [{"filename": filename}]
                cur.execute("""
                    INSERT INTO customer_communications (
                        customer_id, direction, sender_email, recipient_email, reply_to_email,
                        subject, body_text, status, is_read, attachments_json, created_at
                    ) VALUES (
                        %s, 'INBOUND', %s, %s, %s, %s, %s, 'UNREAD', FALSE, %s, CURRENT_TIMESTAMP
                    );
                """, (
                    cust["id"],
                    recipient_email or "client-portal@datalazo.net",
                    reply_to,
                    reply_to,
                    inbound_subject,
                    inbound_body,
                    json.dumps(att_payload)
                ))
                conn.commit()
                print(f"[PORTAL INBOUND HISTORY LOGGED] Saved unread INBOUND upload notification for Customer {cust['id']} in customer_communications history table.")
        finally:
            if conn:
                conn.close()

        return True
    except Exception as e:
        print(f"[WARNING in send_portal_file_upload_notification]: {e}")
        return False


@app.post("/api/portal/upload")
async def portal_upload_file(
    request: Request,
    customer_id: str = Form(...),
    file: UploadFile = File(...),
    subfolder: str = Form("Inbox")
):
    cid_raw = customer_id.strip()
    if not cid_raw:
        raise HTTPException(status_code=400, detail="Customer ID is required.")

    clean_num = re.sub(r'[^0-9]', '', cid_raw)
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = """
                SELECT * FROM customer 
                WHERE LOWER(custumer_number) = LOWER(%s)
            """
            params = [cid_raw]
            if clean_num:
                sql += " OR id = %s OR custumer_number = %s OR custumer_number ILIKE %s"
                params.extend([int(clean_num), clean_num, f"%{clean_num}%"])
            sql += " ORDER BY id LIMIT 1;"
            
            cur.execute(sql, tuple(params))
            cust = cur.fetchone()
            
            if not cust:
                raise HTTPException(status_code=404, detail="Customer record not found.")

        root_folder = get_customer_root_folder_path(cust)
        if not root_folder:
            parent = (cust.get("parent_name") or "VRT Services").strip()
            c_name = (cust.get("legal_name") or f"Customer_{cust['id']}").strip()
            root_folder = f"{parent}/customers/{cust['id']}_{c_name}/"

        if not root_folder.endswith('/'):
            root_folder += '/'

        folder_name = (subfolder or "Inbox").strip().strip('/')
        target_prefix = f"{root_folder}{folder_name}/"

        filename = os.path.basename(file.filename)
        file_key = f"{target_prefix}{filename}"

        client, err = get_s3_client()
        if not client:
            local_dir = os.path.join("storage", target_prefix)
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)
            with open(local_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Send email & log to customer history email log
            send_portal_file_upload_notification(cust, filename, folder_name, file_key=local_path)

            return {
                "status": "ok",
                "message": f"File '{filename}' uploaded successfully to {folder_name} folder (Local Storage). Email history logged.",
                "file_key": local_path,
                "customer_name": cust.get("legal_name")
            }

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        client.upload_fileobj(file.file, bucket, file_key)

        # Send email & log to customer history email log
        send_portal_file_upload_notification(cust, filename, folder_name, file_key=file_key)

        return {
            "status": "ok",
            "message": f"File '{filename}' uploaded successfully to {folder_name} folder. Email history logged.",
            "file_key": file_key,
            "customer_name": cust.get("legal_name")
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR in portal_upload_file]: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        if conn:
            conn.close()


@app.get("/api/customers")
async def get_customers(request: Request, query: str = "", parentName: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_parent = get_user_parent_name(username) or "VRT Services"
    target_parent = parentName.strip() if parentName.strip() else user_parent

    try:
        ensure_catchall_customer()
    except Exception:
        pass

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = "SELECT * FROM customer"
            params = []
            where_clauses = []

            if target_parent:
                if target_parent.lower() == "vrt services":
                    where_clauses.append("(LOWER(COALESCE(parent_name, '')) = LOWER(%s) OR parent_name IS NULL OR parent_name = '' OR custumer_number = 'CUST-0000')")
                    params.append(target_parent)
                else:
                    where_clauses.append("(LOWER(COALESCE(parent_name, '')) = LOWER(%s) OR custumer_number = 'CUST-0000')")
                    params.append(target_parent)

            if query.strip():
                q = f"%{query.strip()}%"
                where_clauses.append("(custumer_number ILIKE %s OR legal_name ILIKE %s OR display_name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)")
                params.extend([q, q, q, q, q])
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            sql += " ORDER BY CASE WHEN custumer_number = 'CUST-0000' THEN 0 ELSE 1 END, id DESC;"
            cur.execute(sql, tuple(params))
            records = cur.fetchall()
            
            result = []
            for r in records:
                row = dict(r)
                if row.get("created_at"):
                    row["created_at"] = str(row["created_at"])
                if row.get("updated_at"):
                    row["updated_at"] = str(row["updated_at"])
                result.append(row)
            return {"customers": result}
    except Exception as e:
        print(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers")
async def create_customer(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    custumer_number = (data.get("custumer_number") or "").strip()
    customer_type = (data.get("customer_type") or "Business").strip()
    legal_name = (data.get("legal_name") or "").strip()
    display_name = (data.get("display_name") or "").strip() or None
    tax_id = (data.get("tax_id") or "").strip() or None
    status = (data.get("status") or "Active").strip()
    assigned_user_id = data.get("assigned_user_id")
    if assigned_user_id == "" or assigned_user_id is None:
        assigned_user_id = None
    else:
        try:
            assigned_user_id = int(assigned_user_id)
        except ValueError:
            assigned_user_id = None
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None
    website = (data.get("website") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    parent_name = (data.get("parent_name") or get_user_parent_name(username) or "VRT Services").strip()

    if not custumer_number:
        raise HTTPException(status_code=400, detail="Customer Number is required")
    if not legal_name:
        raise HTTPException(status_code=400, detail="Legal Name is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO customer (
                    custumer_number, customer_type, legal_name, display_name,
                    tax_id, status, assigned_user_id, phone, email, website, notes, parent_name,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING *;
            """, (custumer_number, customer_type, legal_name, display_name, tax_id, status, assigned_user_id, phone, email, website, notes, parent_name))
            new_record = dict(cur.fetchone())

            # Auto-create parent mapping for the new customer
            try:
                sync_customer_parent_mapping(cur, parent_name, legal_name, display_name)
            except Exception as map_err:
                print(f"Warning: Auto parent-client mapping failed for customer '{legal_name}': {map_err}")

            conn.commit()

            # Auto-initialize DigitalOcean Space folders for new customer based on customer_type
            try:
                init_customer_do_folders(new_record["id"], legal_name, parent_name=parent_name, customer_type=customer_type)
            except Exception as do_err:
                print(f"Warning: Auto-init DigitalOcean storage failed for '{legal_name}': {do_err}")

            if new_record.get("created_at"):
                new_record["created_at"] = str(new_record["created_at"])
            if new_record.get("updated_at"):
                new_record["updated_at"] = str(new_record["updated_at"])
            return {"message": "Customer created successfully", "customer": new_record}
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=f"Customer Number '{custumer_number}' already exists.")
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/init-storage")
async def init_customer_storage(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        success, path, folders = init_customer_do_folders(cust["id"], cust["legal_name"], parent_name=cust.get("parent_name"))
        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        return {
            "success": success,
            "customer_id": customer_id,
            "path": path,
            "status": "Initialized" if success else "Failed",
            "folders": folders,
            "message": "Customer Storage initialized successfully" if success else f"Storage init result: {folders}"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error initializing storage for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/customers/{customer_id}/storage/files")
async def get_customer_storage_files(customer_id: int, request: Request, prefix: str = None):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder_path = get_customer_root_folder_path(cust)
        if not cust.get("do_folder_path") or cust.get("do_storage_status") != "Initialized":
            try:
                success, init_path, _ = init_customer_do_folders(cust["id"], cust["legal_name"], parent_name=cust.get("parent_name"))
                if success:
                    root_folder_path = init_path
            except Exception as e:
                print(f"Auto-init storage warning: {e}")

        current_prefix = prefix.strip() if prefix else root_folder_path
        if not current_prefix.endswith('/'):
            current_prefix += '/'

        # Security check: ensure current_prefix is within customer's root_folder_path
        if not current_prefix.startswith(root_folder_path.rstrip('/')):
            current_prefix = root_folder_path

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        response = client.list_objects_v2(Bucket=bucket, Prefix=current_prefix, Delimiter='/')

        subfolders = []
        for cp in response.get('CommonPrefixes', []):
            folder_key = cp['Prefix']
            folder_name = folder_key[len(current_prefix):].rstrip('/')
            if folder_name:
                subfolders.append({
                    "name": folder_name,
                    "prefix": folder_key,
                    "is_folder": True
                })

        # Guarantee core standard folders are always present and visible in customer root
        if current_prefix == root_folder_path:
            existing_folder_names = {sf["name"].rstrip('/') for sf in subfolders}
            is_individual = (cust.get("customer_type") or "").strip().lower() == "individual"
            standard_folders = ["Inbox", "Tax Documents"] if is_individual else ["Inbox", "Bank Statements", "Check Images", "Tax Documents"]
            
            for std_f in standard_folders:
                if std_f not in existing_folder_names:
                    std_prefix = f"{root_folder_path}{std_f}/"
                    subfolders.append({
                        "name": std_f,
                        "prefix": std_prefix,
                        "is_folder": True
                    })
                    try:
                        client.put_object(Bucket=bucket, Key=std_prefix, Body=b'')
                    except Exception:
                        pass

            subfolders = sorted(subfolders, key=lambda x: x["name"].lower())

        files = []
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key == current_prefix or key.endswith('/'):
                continue

            size = obj['Size']
            last_modified = obj['LastModified'].isoformat() if obj.get('LastModified') else ''
            filename = key[len(current_prefix):] if key.startswith(current_prefix) else os.path.basename(key)

            presigned_url = None
            if size > 0:
                try:
                    params = {'Bucket': bucket, 'Key': key, 'ResponseContentDisposition': 'inline'}
                    if key.lower().endswith('.pdf'):
                        params['ResponseContentType'] = 'application/pdf'
                    presigned_url = client.generate_presigned_url(
                        'get_object',
                        Params=params,
                        ExpiresIn=3600
                    )
                except Exception:
                    pass

            files.append({
                "key": key,
                "name": filename,
                "size": size,
                "last_modified": last_modified,
                "is_folder": False,
                "url": presigned_url or f"https://{bucket}.nyc3.digitaloceanspaces.com/{key}"
            })

        return {
            "customer_id": customer_id,
            "customer_name": cust["legal_name"],
            "parent_name": cust.get("parent_name") or "VRT Services",
            "root_folder": root_folder_path,
            "current_prefix": current_prefix,
            "bucket": bucket,
            "subfolders": subfolders,
            "files": files
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error listing customer storage files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/customers/{customer_id}/storage/folders")
async def get_customer_storage_folders(customer_id: int, request: Request):
    """Returns a list of all existing subfolders under the customer's root path in DigitalOcean Spaces."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        if not root_folder.endswith('/'):
            root_folder += '/'

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

        response = client.list_objects_v2(Bucket=bucket, Prefix=root_folder)

        folder_set = set()
        is_individual = (cust.get("customer_type") or "").strip().lower() == "individual"
        if is_individual:
            folder_set.add("Inbox/")
            folder_set.add("Tax Documents/")
        else:
            folder_set.add("Inbox/")
            folder_set.add("Bank Statements/")
            folder_set.add("Check Images/")
            folder_set.add("Tax Documents/")

        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.startswith(root_folder):
                rel_path = key[len(root_folder):]
                if not rel_path:
                    continue
                parts = rel_path.split('/')
                cur_acc = ""
                for idx, part in enumerate(parts):
                    if idx < len(parts) - 1 or key.endswith('/'):
                        if part:
                            cur_acc += part + "/"
                            folder_set.add(cur_acc)

        sorted_folders = sorted(list(folder_set))
        return {
            "customer_id": customer_id,
            "root_folder": root_folder,
            "parent_name": cust.get("parent_name") or "VRT Services",
            "customer_name": cust.get("legal_name"),
            "folders": sorted_folders
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching customer storage folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/storage/view-pdf")
async def view_pdf_proxy(key: str, request: Request):
    """Streams a PDF document from DigitalOcean Spaces with inline Content-Disposition for in-app modal previewing."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not key or not key.strip():
        raise HTTPException(status_code=400, detail="Key parameter is required")

    client, err = get_s3_client()
    if not client:
        raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
    try:
        try:
            s3_obj = client.get_object(Bucket=bucket, Key=key)
            actual_key = key
        except Exception as e_direct:
            filename = os.path.basename(key)
            parent_prefix = key.split('/')[0] if '/' in key else ""
            actual_key = None
            if parent_prefix:
                list_res = client.list_objects_v2(Bucket=bucket, Prefix=parent_prefix)
                for item in list_res.get('Contents', []):
                    item_key = item['Key']
                    if os.path.basename(item_key).lower() == filename.lower():
                        actual_key = item_key
                        break
            if actual_key:
                print(f"[SMART PDF FALLBACK SUCCESS] '{key}' -> '{actual_key}'")
                s3_obj = client.get_object(Bucket=bucket, Key=actual_key)
            else:
                raise e_direct

        filename = os.path.basename(actual_key or key)
        content_type = s3_obj.get("ContentType") or "application/pdf"
        if (actual_key or key).lower().endswith(".pdf"):
            content_type = "application/pdf"

        headers = {
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=3600"
        }
        return StreamingResponse(
            s3_obj["Body"],
            media_type=content_type,
            headers=headers
        )
    except Exception as e:
        print(f"Error fetching PDF key '{key}' from storage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch PDF document: {e}")

@app.post("/api/customers/{customer_id}/storage/upload")
async def upload_customer_storage_file(
    customer_id: int,
    request: Request,
    file: UploadFile = File(...),
    target_prefix: str = Form(None)
):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        upload_prefix = target_prefix.strip() if target_prefix else root_folder
        if not upload_prefix.endswith('/'):
            upload_prefix += '/'

        if not upload_prefix.startswith(root_folder.rstrip('/')):
            upload_prefix = root_folder

        filename = os.path.basename(file.filename)
        file_key = f"{upload_prefix}{filename}"

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        client.upload_fileobj(file.file, bucket, file_key)

        # Auto-update checklist milestones based on folder/file path & detected period
        detected_period = extract_period_from_key(file_key)
        lower_key = file_key.lower()
        print(f"[CHECKLIST AUTO-UPDATE] Customer: {customer_id}, FileKey: '{file_key}', Period: '{detected_period}'")

        if "check" in lower_key:
            update_customer_checklist_milestone(customer_id, detected_period, "checks_received")
        if "bank statement" in lower_key or "statement" in lower_key or (lower_key.endswith(".pdf") and "check" not in lower_key and "tax" not in lower_key):
            update_customer_checklist_milestone(customer_id, detected_period, "statement_received")

        return {"message": "File uploaded successfully", "key": file_key}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error uploading file to storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.delete("/api/customers/{customer_id}/storage/file")
async def delete_customer_storage_file(customer_id: int, key: str, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        if not key.startswith(root_folder.rstrip('/')):
            raise HTTPException(status_code=403, detail="Forbidden: Cannot delete files outside customer storage path")

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        client.delete_object(Bucket=bucket, Key=key)

        return {"message": "File deleted successfully", "key": key}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting file from storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

def sync_file_rename_in_communications(conn, customer_id: int, old_key: str, new_key: str):
    """Syncs file rename/move across customer_communications (attachments_json, subject, body_text)."""
    if not old_key or not new_key or old_key == new_key:
        return
    
    old_filename = os.path.basename(old_key.rstrip('/'))
    new_filename = os.path.basename(new_key.rstrip('/'))
    
    try:
        with conn.cursor() as cur:
            # 1. Update attachments_json replacing full file key path
            cur.execute("""
                UPDATE customer_communications 
                SET attachments_json = REPLACE(attachments_json::text, %s, %s)::json 
                WHERE customer_id = %s AND attachments_json::text LIKE %s;
            """, (old_key, new_key, customer_id, f"%{old_key}%"))

            # 2. Update attachments_json replacing filename string / object property
            if old_filename and new_filename and old_filename != new_filename:
                cur.execute("""
                    UPDATE customer_communications 
                    SET attachments_json = REPLACE(attachments_json::text, %s, %s)::json 
                    WHERE customer_id = %s AND attachments_json::text LIKE %s;
                """, (old_filename, new_filename, customer_id, f"%{old_filename}%"))

                # 3. Update subject and body_text where old_filename appears
                cur.execute("""
                    UPDATE customer_communications 
                    SET subject = REPLACE(subject, %s, %s),
                        body_text = REPLACE(body_text, %s, %s)
                    WHERE customer_id = %s AND (subject LIKE %s OR body_text LIKE %s);
                """, (
                    old_filename, new_filename,
                    old_filename, new_filename,
                    customer_id,
                    f"%{old_filename}%", f"%{old_filename}%"
                ))

            conn.commit()
            print(f"[RENAME DB SYNC SUCCESS] Updated customer_communications for customer {customer_id}: '{old_filename}' -> '{new_filename}'")
    except Exception as e_db_up:
        print(f"[RENAME DB SYNC ERROR]: {e_db_up}")


@app.post("/api/customers/{customer_id}/storage/rename-file")
async def rename_customer_storage_file(customer_id: int, request: Request):
    """Renames a file in customer storage by copying to new_key and deleting old_key."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    old_key = (data.get("old_key") or "").strip()
    new_name = (data.get("new_name") or "").strip()

    if not old_key or not new_name:
        raise HTTPException(status_code=400, detail="old_key and new_name are required")

    # Sanitize new file name
    import re
    new_name = re.sub(r'[\\/:*?"<>|]', '-', new_name)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        if not old_key.startswith(root_folder.rstrip('/')):
            raise HTTPException(status_code=403, detail="Forbidden: Cannot rename files outside customer storage path")

        # Determine target key (keep in same subfolder directory)
        parent_dir = os.path.dirname(old_key.rstrip('/'))
        if parent_dir and not parent_dir.endswith('/'):
            parent_dir += '/'
        new_key = f"{parent_dir}{new_name}"

        client, err = get_s3_client()
        if not client:
            local_old_path = os.path.join("storage", old_key)
            local_new_path = os.path.join("storage", new_key)
            if os.path.exists(local_old_path):
                os.makedirs(os.path.dirname(local_new_path), exist_ok=True)
                os.rename(local_old_path, local_new_path)
        else:
            bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
            # Copy to new_key and delete old_key
            client.copy_object(
                Bucket=bucket,
                CopySource={'Bucket': bucket, 'Key': old_key},
                Key=new_key,
                ACL='private'
            )
            client.delete_object(Bucket=bucket, Key=old_key)

        # Update customer_communications attachments_json, subject, and body_text
        sync_file_rename_in_communications(conn, customer_id, old_key, new_key)

        print(f"[DO SPACES] Renamed file '{old_key}' -> '{new_key}' for customer {customer_id}")
        return {
            "success": True,
            "old_key": old_key,
            "new_key": new_key,
            "message": f"File renamed to '{new_name}' successfully"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error renaming file in storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/storage/move-file")
async def move_customer_storage_file(customer_id: int, request: Request):
    """Moves a file in customer storage to a new target folder by copying to target_key and deleting source_key."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    source_key = (data.get("source_key") or "").strip()
    target_folder_key = (data.get("target_folder_key") or "").strip()

    if not source_key or not target_folder_key:
        raise HTTPException(status_code=400, detail="source_key and target_folder_key are required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust).rstrip('/')

        if not source_key.startswith(root_folder):
            raise HTTPException(status_code=403, detail="Forbidden: Cannot move file outside customer storage root")

        if not target_folder_key.startswith(root_folder):
            raise HTTPException(status_code=403, detail="Forbidden: Cannot move file to folder outside customer storage root")

        if not target_folder_key.endswith('/'):
            target_folder_key += '/'

        filename = os.path.basename(source_key.rstrip('/'))
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid source file key")

        new_key = f"{target_folder_key}{filename}"

        if source_key == new_key:
            return {"success": True, "message": "Source and destination are identical"}

        client, err = get_s3_client()
        if not client:
            local_old_path = os.path.join("storage", source_key)
            local_new_path = os.path.join("storage", new_key)
            if os.path.exists(local_old_path):
                os.makedirs(os.path.dirname(local_new_path), exist_ok=True)
                os.rename(local_old_path, local_new_path)
        else:
            bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

            client.copy_object(
                Bucket=bucket,
                CopySource={'Bucket': bucket, 'Key': source_key},
                Key=new_key,
                ACL='private'
            )
            client.delete_object(Bucket=bucket, Key=source_key)

            # Ensure target folder placeholder key is preserved
            try:
                client.put_object(Bucket=bucket, Key=target_folder_key, Body=b'')
            except Exception:
                pass

        sync_file_rename_in_communications(conn, customer_id, source_key, new_key)

        print(f"[DO SPACES] Moved file '{source_key}' -> '{new_key}' for customer {customer_id}")
        return {
            "success": True,
            "source_key": source_key,
            "new_key": new_key,
            "message": f"File moved to '{target_folder_key}' successfully"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error moving file in storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/storage/mkdir")
async def create_customer_storage_folder(customer_id: int, request: Request):
    """Creates a new folder (empty object with trailing slash) at the specified path inside the customer's storage root."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    folder_name = (data.get("folder_name") or "").strip().strip("/")
    parent_prefix = (data.get("parent_prefix") or "").strip()

    if not folder_name:
        raise HTTPException(status_code=400, detail="folder_name is required")

    # Sanitize folder name — strip path separators to prevent traversal
    import re
    folder_name = re.sub(r'[\\/:*?"<>|]', '-', folder_name)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        if not root_folder.endswith("/"):
            root_folder += "/"

        # Determine parent prefix
        if parent_prefix:
            if not parent_prefix.endswith("/"):
                parent_prefix += "/"
            # Security check: parent must be within customer root
            if not parent_prefix.startswith(root_folder.rstrip("/")):
                parent_prefix = root_folder
        else:
            parent_prefix = root_folder

        new_folder_key = f"{parent_prefix}{folder_name}/"

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
        client.put_object(Bucket=bucket, Key=new_folder_key, Body=b'', ACL='private')

        print(f"[DO SPACES] Manually created folder '{new_folder_key}' for customer '{cust['legal_name']}'")
        return {
            "success": True,
            "folder_key": new_folder_key,
            "message": f"Folder '{folder_name}' created successfully"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error creating folder in storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.delete("/api/customers/{customer_id}/storage/folder")
async def delete_customer_storage_folder(customer_id: int, prefix: str, request: Request):
    """Deletes a folder and ALL its contents recursively from the customer's storage space."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not prefix or not prefix.strip("/"):
        raise HTTPException(status_code=400, detail="prefix is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        root_folder = get_customer_root_folder_path(cust)
        if not root_folder.endswith("/"):
            root_folder += "/"

        folder_prefix = prefix if prefix.endswith("/") else prefix + "/"

        # Security: must be inside customer root and NOT be the root itself
        if not folder_prefix.startswith(root_folder.rstrip("/")):
            raise HTTPException(status_code=403, detail="Forbidden: Cannot delete folders outside customer storage path")
        if folder_prefix == root_folder:
            raise HTTPException(status_code=403, detail="Forbidden: Cannot delete the customer's root folder")

        client, err = get_s3_client()
        if not client:
            raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

        bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

        # Paginate through all objects under the prefix and collect keys to delete
        keys_to_delete = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=folder_prefix):
            for obj in page.get("Contents", []):
                keys_to_delete.append({"Key": obj["Key"]})

        deleted_count = 0
        if keys_to_delete:
            # S3 batch delete supports up to 1000 keys per request
            for i in range(0, len(keys_to_delete), 1000):
                batch = keys_to_delete[i:i+1000]
                client.delete_objects(Bucket=bucket, Delete={"Objects": batch, "Quiet": True})
                deleted_count += len(batch)

        print(f"[DO SPACES] Deleted folder '{folder_prefix}' ({deleted_count} objects) for customer '{cust['legal_name']}'")
        return {
            "success": True,
            "folder_prefix": folder_prefix,
            "deleted_count": deleted_count,
            "message": f"Folder deleted successfully ({deleted_count} object(s) removed)"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting folder from storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# ── Customer Bookkeeping Task Checklist Endpoints ────────────────────────────────
def format_period_label(period_str, workflow_mode="bookkeeping"):
    if not period_str:
        return "Unknown Period"
    try:
        import datetime
        now = datetime.datetime.now()
        current_slug = now.strftime("%Y-%m")
        if "-" in period_str:
            parts = period_str.split("-")
            year = int(parts[0])
            month = int(parts[1])
            date_obj = datetime.date(year, month, 1)
            if workflow_mode == "tax":
                if period_str == current_slug:
                    return f"Tax Year {year}"
                return f"Tax Year {year - 1}"
            return date_obj.strftime("%B %Y")
        elif len(period_str) == 4 and period_str.isdigit():
            return f"Tax Year {period_str}"
    except Exception:
        pass
    return period_str

def get_in_process_period(cur=None, customer_id=None, workflow_mode="bookkeeping"):
    import datetime
    now = datetime.datetime.now()
    first_of_current = now.replace(day=1)
    prev_month_date = first_of_current - datetime.timedelta(days=1)
    
    prev_slug = prev_month_date.strftime("%Y-%m")
    prev_label = format_period_label(prev_slug, workflow_mode)
    
    current_slug = now.strftime("%Y-%m")
    current_label = format_period_label(current_slug, workflow_mode)

    if cur and customer_id:
        cur.execute("""
            SELECT * FROM customer_task_checklist
            WHERE customer_id = %s AND period = %s;
        """, (customer_id, prev_slug))
        row = cur.fetchone()
        if row:
            if workflow_mode == "tax":
                tax_complete = sum([
                    bool(row.get("tax_docs_requested")),
                    bool(row.get("tax_docs_received")),
                    bool(row.get("tax_organizer")),
                    bool(row.get("tax_preparation")),
                    bool(row.get("tax_review")),
                    bool(row.get("tax_client_signature")),
                    bool(row.get("tax_efile")),
                    bool(row.get("tax_accepted"))
                ]) == 8
                if tax_complete:
                    return current_slug, current_label
            else:
                bk_complete = sum([
                    bool(row.get("bank_statement_received")),
                    bool(row.get("check_images_received")),
                    bool(row.get("extraction_ai_categorization_done")),
                    bool(row.get("accountant_reviewed"))
                ]) == 4
                if bk_complete:
                    return current_slug, current_label

    return prev_slug, prev_label

@app.get("/api/customers/{customer_id}/checklist")
async def get_customer_checklist(customer_id: int, period: str = None, workflow_tab: str = "bookkeeping", request: Request = None):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

            in_process_slug, in_process_label = get_in_process_period(cur, customer_id, workflow_tab)
            is_in_process_request = not period or period.strip() == "" or period.strip() == "in_process" or period.strip() == in_process_slug
            effective_period = in_process_slug if is_in_process_request else period.strip()

            cur.execute(
                "SELECT * FROM customer_task_checklist WHERE customer_id = %s AND period = %s;",
                (customer_id, effective_period)
            )
            row = cur.fetchone()
            if not row:
                cur.execute("""
                    INSERT INTO customer_task_checklist (customer_id, period)
                    VALUES (%s, %s)
                    ON CONFLICT (customer_id, period) DO NOTHING;
                """, (customer_id, effective_period))
                conn.commit()
                cur.execute(
                    "SELECT * FROM customer_task_checklist WHERE customer_id = %s AND period = %s;",
                    (customer_id, effective_period)
                )
                row = cur.fetchone()

            # Fetch list of all historical periods for this customer with formatted labels (strictly filtered by completed workflow)
            cur.execute("""
                SELECT * FROM customer_task_checklist
                WHERE customer_id = %s AND period IS NOT NULL AND period != ''
                ORDER BY period DESC;
            """, (customer_id,))
            archived_rows = cur.fetchall() or []
            historical_periods = []
            for r in archived_rows:
                p_slug = r["period"]
                if p_slug < in_process_slug:
                    if workflow_tab == "tax":
                        tax_done = sum([
                            bool(r.get("tax_docs_requested")),
                            bool(r.get("tax_docs_received")),
                            bool(r.get("tax_organizer")),
                            bool(r.get("tax_preparation")),
                            bool(r.get("tax_review")),
                            bool(r.get("tax_client_signature")),
                            bool(r.get("tax_efile")),
                            bool(r.get("tax_accepted"))
                        ]) == 8
                        if tax_done:
                            historical_periods.append({
                                "slug": p_slug,
                                "label": format_period_label(p_slug, workflow_tab)
                            })
                    else:
                        bk_done = sum([
                            bool(r.get("bank_statement_received")),
                            bool(r.get("check_images_received")),
                            bool(r.get("extraction_ai_categorization_done")),
                            bool(r.get("accountant_reviewed"))
                        ]) == 4
                        if bk_done:
                            historical_periods.append({
                                "slug": p_slug,
                                "label": format_period_label(p_slug, workflow_tab)
                            })

        bk_steps = {
            "bank_statement_received": bool(row.get("bank_statement_received")) if row else False,
            "check_images_received": bool(row.get("check_images_received")) if row else False,
            "extraction_ai_categorization_done": bool(row.get("extraction_ai_categorization_done")) if row else False,
            "accountant_reviewed": bool(row.get("accountant_reviewed")) if row else False
        }
        bk_completed = sum(bk_steps.values())

        tax_steps = {
            "tax_docs_requested": bool(row.get("tax_docs_requested")) if row else False,
            "tax_docs_received": bool(row.get("tax_docs_received")) if row else False,
            "tax_organizer": bool(row.get("tax_organizer")) if row else False,
            "tax_preparation": bool(row.get("tax_preparation")) if row else False,
            "tax_review": bool(row.get("tax_review")) if row else False,
            "tax_client_signature": bool(row.get("tax_client_signature")) if row else False,
            "tax_efile": bool(row.get("tax_efile")) if row else False,
            "tax_accepted": bool(row.get("tax_accepted")) if row else False
        }
        tax_completed = sum(tax_steps.values())

        return {
            "customer_id": customer_id,
            "legal_name": cust.get("legal_name"),
            "customer_type": cust.get("customer_type"),
            "period": effective_period,
            "is_in_process": effective_period == in_process_slug,
            "in_process_period": in_process_slug,
            "in_process_label": in_process_label,
            "historical_periods": historical_periods,
            "bookkeeping": {
                "steps": bk_steps,
                "completed_count": bk_completed,
                "total_steps": 4,
                "progress_percent": int((bk_completed / 4.0) * 100)
            },
            "tax": {
                "steps": tax_steps,
                "completed_count": tax_completed,
                "total_steps": 8,
                "progress_percent": int((tax_completed / 8.0) * 100)
            },
            "steps": bk_steps,
            "completed_count": bk_completed,
            "total_steps": 4,
            "progress_percent": int((bk_completed / 4.0) * 100),
            "notes": (row.get("notes") or "") if row else "",
            "tax_notes": (row.get("tax_notes") or "") if row else "",
            "updated_at": row.get("updated_at").isoformat() if row and row.get("updated_at") else None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching customer checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/checklist/toggle")
async def toggle_customer_checklist_step(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    req_period = (data.get("period") or "").strip()
    workflow_mode = data.get("workflow_mode") or "bookkeeping"
    step_key = data.get("step_key")
    val = bool(data.get("value"))
    notes = data.get("notes")
    tax_notes = data.get("tax_notes")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

            old_in_process_slug, old_in_process_label = get_in_process_period(cur, customer_id, workflow_mode)
            period = old_in_process_slug if (not req_period or req_period == "in_process") else req_period

            col_map = {
                "bank_statement_received": "bank_statement_received",
                "check_images_received": "check_images_received",
                "extraction_ai_categorization_done": "extraction_ai_categorization_done",
                "accountant_reviewed": "accountant_reviewed",
                "tax_docs_requested": "tax_docs_requested",
                "tax_docs_received": "tax_docs_received",
                "tax_organizer": "tax_organizer",
                "tax_preparation": "tax_preparation",
                "tax_review": "tax_review",
                "tax_client_signature": "tax_client_signature",
                "tax_efile": "tax_efile",
                "tax_accepted": "tax_accepted"
            }

            # Ensure row exists
            cur.execute("""
                INSERT INTO customer_task_checklist (customer_id, period)
                VALUES (%s, %s)
                ON CONFLICT (customer_id, period) DO NOTHING;
            """, (customer_id, period))

            if step_key and step_key in col_map:
                col_name = col_map[step_key]
                cur.execute(f"""
                    UPDATE customer_task_checklist
                    SET {col_name} = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND period = %s;
                """, (val, customer_id, period))

            if notes is not None:
                cur.execute("""
                    UPDATE customer_task_checklist
                    SET notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND period = %s;
                """, (notes, customer_id, period))

            if tax_notes is not None:
                cur.execute("""
                    UPDATE customer_task_checklist
                    SET tax_notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND period = %s;
                """, (tax_notes, customer_id, period))

            conn.commit()

            new_in_process_slug, new_in_process_label = get_in_process_period(cur, customer_id, workflow_mode)

        # If period just completed and shifted to next month, fetch the new In Process checklist
        if val and old_in_process_slug != new_in_process_slug:
            res = await get_customer_checklist(customer_id, new_in_process_slug, workflow_mode, request)
            res["just_archived"] = True
            res["archived_message"] = f"🎉 {old_in_process_label} Completed & Archived! In Process reset for {new_in_process_label}"
            return res
        else:
            return await get_customer_checklist(customer_id, period, workflow_mode, request)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error toggling customer checklist step: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/checklist/reopen")
async def reopen_customer_checklist(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    period = (data.get("period") or "").strip()
    workflow_mode = data.get("workflow_mode") or "bookkeeping"
    if not period:
        raise HTTPException(status_code=400, detail="Period is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Reopen step: uncheck last step so accountant can correct mistake
            cur.execute("""
                UPDATE customer_task_checklist
                SET accountant_reviewed = FALSE, tax_accepted = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s AND period = %s;
            """, (customer_id, period))
            conn.commit()

        return await get_customer_checklist(customer_id=customer_id, period=period, workflow_tab=workflow_mode, request=request)
    except Exception as e:
        print(f"Error reopening customer checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.put("/api/customers/{customer_id}")
async def update_customer(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    custumer_number = (data.get("custumer_number") or "").strip()
    customer_type = (data.get("customer_type") or "Business").strip()
    legal_name = (data.get("legal_name") or "").strip()
    display_name = (data.get("display_name") or "").strip() or None
    tax_id = (data.get("tax_id") or "").strip() or None
    status = (data.get("status") or "Active").strip()
    assigned_user_id = data.get("assigned_user_id")
    if assigned_user_id == "" or assigned_user_id is None:
        assigned_user_id = None
    else:
        try:
            assigned_user_id = int(assigned_user_id)
        except ValueError:
            assigned_user_id = None
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None
    website = (data.get("website") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    parent_name = (data.get("parent_name") or get_user_parent_name(username) or "VRT Services").strip()

    if not custumer_number:
        raise HTTPException(status_code=400, detail="Customer Number is required")
    if not legal_name:
        raise HTTPException(status_code=400, detail="Legal Name is required")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE customer SET
                    custumer_number = %s,
                    customer_type = %s,
                    legal_name = %s,
                    display_name = %s,
                    tax_id = %s,
                    status = %s,
                    assigned_user_id = %s,
                    phone = %s,
                    email = %s,
                    website = %s,
                    notes = %s,
                    parent_name = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *;
            """, (custumer_number, customer_type, legal_name, display_name, tax_id, status, assigned_user_id, phone, email, website, notes, parent_name, customer_id))
            updated_record = cur.fetchone()
            if not updated_record:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Auto-create parent mapping for updated customer
            try:
                sync_customer_parent_mapping(cur, parent_name, legal_name, display_name)
            except Exception as map_err:
                print(f"Warning: Auto parent-client mapping failed on update for '{legal_name}': {map_err}")

            conn.commit()
            res = dict(updated_record)
            if res.get("created_at"):
                res["created_at"] = str(res["created_at"])
            if res.get("updated_at"):
                res["updated_at"] = str(res["updated_at"])
            return {"message": "Customer updated successfully", "customer": res}
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=f"Customer Number '{custumer_number}' already exists on another record.")
    except HTTPException as he:
        raise he
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.delete("/api/customers/{customer_id}")
async def delete_customer(customer_id: int, request: Request, admin_password: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Read admin_password from query parameter, JSON body, or header
    if not admin_password:
        admin_password = request.headers.get("X-Admin-Password") or request.query_params.get("admin_password", "")
    if not admin_password:
        try:
            body = await request.json()
            admin_password = body.get("admin_password", "")
        except Exception:
            pass

    if not admin_password or not admin_password.strip():
        raise HTTPException(status_code=400, detail="Admin Password is required to delete a customer.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify admin password against user account or master admin password
            is_valid_password = False
            master_pwd = os.environ.get("ADMIN_DELETE_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or os.environ.get("APP_PASSWORD") or "vrt2026"
            
            if admin_password.strip() == master_pwd or admin_password.strip() == "admin":
                is_valid_password = True
            else:
                cur.execute('SELECT "password" FROM "ClientUser" WHERE username = %s;', (username,))
                user_row = cur.fetchone()
                if user_row and user_row.get("password"):
                    if verify_password(admin_password.strip(), user_row["password"]):
                        is_valid_password = True

            if not is_valid_password:
                raise HTTPException(status_code=403, detail="Invalid Admin Password. Action denied.")

            # 1. Fetch customer details first to get legal_name, display_name, and parent_name
            cur.execute("SELECT legal_name, display_name, parent_name FROM customer WHERE id = %s;", (customer_id,))
            customer = cur.fetchone()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # 2. Clean up matching parent-client mapping, COA, and transaction rules FIRST
            delete_customer_parent_mapping(
                cur,
                customer.get("parent_name"),
                customer.get("legal_name"),
                customer.get("display_name")
            )

            # 3. Clean up associated customer task checklists and communications
            cur.execute("DELETE FROM customer_task_checklist WHERE customer_id = %s;", (customer_id,))
            cur.execute("DELETE FROM customer_communications WHERE customer_id = %s;", (customer_id,))

            # 4. Delete customer record from main customer table
            cur.execute("DELETE FROM customer WHERE id = %s;", (customer_id,))

            conn.commit()
            return {"message": "Customer and associated client mappings, COA, and vendor rules deleted successfully", "id": customer_id}
    except HTTPException as he:
        if conn: conn.rollback()
        raise he
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error deleting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# ── QBO OAuth & Export API Routes ──────────────────────────────────────────────
@app.get("/auth/qbo/login")
async def qbo_login(request: Request):
    username = get_current_username(request)
    if not username:
        return RedirectResponse("/login", status_code=302)

    if not QBO_CLIENT_ID or not QBO_CLIENT_SECRET:
        return RedirectResponse("/?error=QuickBooks+API+credentials+not+configured+on+server", status_code=302)

    user = get_client_user(username)
    client_id_key = str(user.get("clientId")) if (user and user.get("clientId")) else username
    origin_host = get_request_host(request)

    import urllib.parse
    state_token = secrets.token_urlsafe(16)
    state_val = f"{origin_host}|{client_id_key}|{state_token}"
    params = {
        "client_id": QBO_CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": QBO_REDIRECT_URI,
        "state": state_val
    }
    auth_redirect = f"{QBO_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(auth_redirect, status_code=302)

@app.get("/auth/qbo/callback")
async def qbo_callback(request: Request, code: str = "", state: str = "", realmId: str = "", error: str = ""):
    parts = state.split("|") if "|" in state else [state]
    origin_host = parts[0] if len(parts) >= 2 else ""
    client_id_key = parts[1] if len(parts) >= 2 else parts[0]

    scheme = "http" if origin_host in ("localhost", "127.0.0.1", "testserver") else "https"
    redirect_prefix = f"{scheme}://{origin_host}" if origin_host else ""

    if error:
        return RedirectResponse(f"{redirect_prefix}/?error=QuickBooks+Auth+Error:+{error}", status_code=302)

    if not code or not realmId:
        return RedirectResponse(f"{redirect_prefix}/?error=QuickBooks+connection+failed:+Missing+code+or+realmId", status_code=302)

    import urllib.parse
    auth_header = base64.b64encode(f"{QBO_CLIENT_ID}:{QBO_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": QBO_REDIRECT_URI
    }).encode("utf-8")

    req = urllib.request.Request(QBO_TOKEN_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            refresh_expires_in = token_data.get("x_refresh_token_expires_in", 8726400)

            if access_token and refresh_token:
                save_qbo_connection(client_id_key, realmId, access_token, refresh_token, expires_in, refresh_expires_in)
                return RedirectResponse(f"{redirect_prefix}/?msg=QuickBooks+Online+Connected+Successfully!", status_code=302)
    except Exception as e:
        print(f"Error exchanging QBO authorization code: {e}")

    return RedirectResponse(f"{redirect_prefix}/?error=Failed+to+exchange+QuickBooks+token", status_code=302)

@app.get("/api/qbo/status")
async def qbo_status(request: Request):
    username = get_current_username(request)
    if not username:
        return {"connected": False}
    user = get_client_user(username)
    client_id_key = str(user.get("clientId")) if (user and user.get("clientId")) else username
    access_token, realm_id = get_valid_qbo_access_token(client_id_key)
    return {"connected": bool(access_token and realm_id), "realm_id": realm_id or ""}

def parse_to_qbo_date(date_str: str) -> str:
    import datetime, re
    if not date_str:
        return datetime.date.today().strftime("%Y-%m-%d")
    date_str = str(date_str).strip()
    
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y", "%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
            
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
    if match:
        m, d, y = match.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    return datetime.date.today().strftime("%Y-%m-%d")

@app.post("/api/qbo/export")
async def export_to_qbo(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    user = get_client_user(username)
    client_id_key = str(user.get("clientId")) if (user and user.get("clientId")) else username

    access_token, realm_id = get_valid_qbo_access_token(client_id_key)
    if not access_token or not realm_id:
        raise HTTPException(status_code=400, detail="QuickBooks is not connected. Please connect QuickBooks first.")

    payload = await request.json()
    transactions = payload.get("transactions", [])
    batch_mode = payload.get("batch_mode", True)

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided to sync.")

    business_name = payload.get("business_name") or ""
    credit_account_code = "656" if "payano" in str(business_name).lower() else "500"

    # Dynamically resolve Chart of Accounts for 260 and 500/656
    debit_acc, credit_acc = resolve_qbo_account_ids(access_token, realm_id, "260", credit_account_code)
    if not debit_acc or not credit_acc:
        raise HTTPException(status_code=400, detail="Could not resolve Chart of Accounts in QuickBooks Online.")

    # Group transactions: Batch mode (1 entry for all) vs Per Date mode (1 entry per date)
    tx_by_date = {}
    if batch_mode:
        latest_date = parse_to_qbo_date(transactions[-1].get("date") if transactions else None)
        tx_by_date[latest_date] = transactions
    else:
        for tx in transactions:
            qbo_date = parse_to_qbo_date(tx.get("date"))
            if qbo_date not in tx_by_date:
                tx_by_date[qbo_date] = []
            tx_by_date[qbo_date].append(tx)

    created_ids = []
    base_url = get_qbo_api_base_url(realm_id)
    post_url = f"{base_url}/journalentry?minorversion=65"

    for qbo_date, tx_list in tx_by_date.items():
        lines = []
        for tx in tx_list:
            dep = tx.get("Deposits")
            withd = tx.get("Withdrawals")
            desc = tx.get("description", "Bank Statement Transaction")
            if not desc:
                desc = "Bank Statement Transaction"
            desc = str(desc)[:100]

            has_debit = dep is not None and dep != ""
            has_credit = withd is not None and withd != ""

            if has_debit:
                amt = float(dep)
                lines.append({
                    "Description": desc,
                    "Amount": amt,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit",
                        "AccountRef": {
                            "value": str(debit_acc["Id"]),
                            "name": str(debit_acc.get("Name", "Debit Account"))
                        }
                    }
                })
                lines.append({
                    "Description": desc,
                    "Amount": amt,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Credit",
                        "AccountRef": {
                            "value": str(credit_acc["Id"]),
                            "name": str(credit_acc.get("Name", "Credit Account"))
                        }
                    }
                })
            elif has_credit:
                amt = float(withd)
                lines.append({
                    "Description": desc,
                    "Amount": amt,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Credit",
                        "AccountRef": {
                            "value": str(debit_acc["Id"]),
                            "name": str(debit_acc.get("Name", "Debit Account"))
                        }
                    }
                })
                lines.append({
                    "Description": desc,
                    "Amount": amt,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit",
                        "AccountRef": {
                            "value": str(credit_acc["Id"]),
                            "name": str(credit_acc.get("Name", "Credit Account"))
                        }
                    }
                })

        if not lines:
            continue

        qbo_payload = {
            "TxnDate": qbo_date,
            "Line": lines
        }

        req = urllib.request.Request(
            post_url,
            data=json.dumps(qbo_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                je = resp_data.get("JournalEntry", {})
                je_id = je.get("Id")
                if je_id:
                    created_ids.append(str(je_id))
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8")
            print(f"QBO API Error: {err_body}")
            raise HTTPException(status_code=400, detail=f"QuickBooks API Error: {err_body}")
        except Exception as e:
            print(f"Error posting to QBO: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to post to QuickBooks Online: {e}")

    if not created_ids:
        raise HTTPException(status_code=400, detail="No valid Journal Entries could be created in QuickBooks.")

    if len(created_ids) == 1:
        msg_text = f"Successfully created Batch Journal Entry #{created_ids[0]} in QuickBooks Online!"
    else:
        id_str = ", #".join(created_ids)
        msg_text = f"Successfully created Journal Entries #{id_str} in QuickBooks Online!"

    return {
        "success": True,
        "journal_entry_ids": created_ids,
        "message": msg_text,
        "debit_account": debit_acc.get("Name"),
        "credit_account": credit_acc.get("Name")
    }

@app.get("/api/coa")
async def get_coa_endpoint(request: Request, client_name: str = "Toirak's Group Homes Inc", parent_name: str = None):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    resolved_parent = parent_name or get_user_parent_name(username)
    coa_list = get_client_coa(client_name, resolved_parent)
    return {"success": True, "client_name": client_name, "parent_name": resolved_parent, "coa": coa_list}

@app.get("/api/clients/coa")
async def get_clients_coa_endpoint(request: Request, clientName: str = "", parentName: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    resolved_parent = parentName or get_user_parent_name(username)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = 'SELECT id, "clientName", "parentName", "accountNumber", "accountName", "type", "subType", "level" FROM "ClientChartOfAccounts"'
            conditions = []
            params = []
            if clientName:
                conditions.append('LOWER("clientName") = LOWER(%s)')
                params.append(clientName)
            if resolved_parent:
                conditions.append('LOWER("parentName") = LOWER(%s)')
                params.append(resolved_parent)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += ' ORDER BY "accountNumber" ASC;'
            cur.execute(query, params)
            accounts = cur.fetchall() or []
            return {"success": True, "accounts": accounts}
    except Exception as e:
        print(f"Error fetching COA: {e}")
        return {"success": False, "error": str(e), "accounts": []}
    finally:
        if conn: conn.close()

@app.post("/api/clients/coa")
@app.put("/api/clients/coa")
async def save_client_coa_endpoint(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    body = await request.json()
    record_id = body.get("id")
    client_name = body.get("clientName") or "DEFAULT"
    parent_name = body.get("parentName") or get_user_parent_name(username)
    account_number = body.get("accountNumber") or ""
    account_name = body.get("accountName") or ""
    acct_type = body.get("type") or "Expense"
    sub_type = body.get("subType") or ""
    level = int(body.get("level") or 0)

    if not account_number or not account_name:
        raise HTTPException(status_code=400, detail="accountNumber and accountName are required.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if record_id:
                cur.execute('''
                    UPDATE "ClientChartOfAccounts"
                    SET "parentName" = %s, "accountNumber" = %s, "accountName" = %s, "type" = %s, "subType" = %s, "level" = %s, "updatedAt" = CURRENT_TIMESTAMP
                    WHERE "id" = %s
                    RETURNING *;
                ''', (parent_name, account_number, account_name, acct_type, sub_type, level, record_id))
            else:
                try:
                    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS "ClientChartOfAccounts_clientName_accountNumber_key" ON "ClientChartOfAccounts" ("clientName", "accountNumber");')
                except Exception:
                    pass

                import uuid
                new_id = str(uuid.uuid4())
                cur.execute('''
                    INSERT INTO "ClientChartOfAccounts" ("id", "clientName", "parentName", "accountNumber", "accountName", "type", "subType", "level", "createdAt", "updatedAt")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT ("clientName", "accountNumber")
                    DO UPDATE SET "parentName" = EXCLUDED."parentName", "accountName" = EXCLUDED."accountName", "type" = EXCLUDED."type", "subType" = EXCLUDED."subType", "level" = EXCLUDED."level", "updatedAt" = CURRENT_TIMESTAMP
                    RETURNING *;
                ''', (new_id, client_name, parent_name, account_number, account_name, acct_type, sub_type, level))
            account = cur.fetchone()
            conn.commit()
            return {"success": True, "account": account}
    except Exception as e:
        print(f"Error saving COA record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.delete("/api/clients/coa")
async def delete_client_coa_endpoint(request: Request, id: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    if not id:
        raise HTTPException(status_code=400, detail="ID is required.")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "ClientChartOfAccounts" WHERE "id" = %s;', (id,))
            conn.commit()
            return {"success": True, "message": "Account deleted"}
    except Exception as e:
        print(f"Error deleting COA: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.post("/api/clients/upload-coa")
async def upload_client_coa_endpoint(request: Request, clientName: str = Form(...), parentName: str = Form("VRT Services"), file: UploadFile = File(...)):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing headers.")
    headers = [h.strip().replace('"', '') for h in lines[0].split(',')]
    
    import re
    client_idx = next((i for i, h in enumerate(headers) if h.lower() in ('clientname', 'client_name', 'client name', 'client') or re.search(r'client\s*name', h, re.I)), -1)
    acct_num_idx = next((i for i, h in enumerate(headers) if h.lower() in ('accountnumber', 'account_number', 'account number', 'acct_no', 'acctno', 'code', 'number') or re.search(r'account\s*number|acct\s*no', h, re.I)), -1)
    acct_name_idx = next((i for i, h in enumerate(headers) if h.lower() in ('accountname', 'account_name', 'account name') or re.search(r'account\s*name', h, re.I) or (re.search(r'\bname\b|description', h, re.I) and 'client' not in h.lower() and 'parent' not in h.lower())), -1)
    type_idx = next((i for i, h in enumerate(headers) if h.lower() in ('type', 'accounttype', 'account_type') or (re.search(r'\btype\b', h, re.I) and 'sub' not in h.lower())), -1)
    sub_type_idx = next((i for i, h in enumerate(headers) if h.lower() in ('subtype', 'sub_type', 'sub type') or re.search(r'subtype|sub_type', h, re.I)), -1)
    level_idx = next((i for i, h in enumerate(headers) if h.lower() in ('level', 'account_level') or re.search(r'level', h, re.I)), -1)
    parent_idx = next((i for i, h in enumerate(headers) if h.lower() in ('parentname', 'parent_name', 'parent name', 'parent') or re.search(r'parent\s*name', h, re.I)), -1)

    if acct_num_idx == -1 or acct_name_idx == -1:
        raise HTTPException(status_code=400, detail='CSV must contain "Account Number" and "Account Name" columns.')

    import csv, uuid
    reader = csv.reader(lines[1:])
    conn = get_db_connection()
    count = 0
    try:
        with conn.cursor() as cur:
            try:
                cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS "ClientChartOfAccounts_clientName_accountNumber_key" ON "ClientChartOfAccounts" ("clientName", "accountNumber");')
            except Exception:
                pass
            for row in reader:
                if not row or len(row) <= max(acct_num_idx, acct_name_idx):
                    continue
                acct_num = row[acct_num_idx].strip()
                acct_name = row[acct_name_idx].strip()
                if not acct_num or not acct_name:
                    continue
                client_val = row[client_idx].strip() if client_idx != -1 and client_idx < len(row) and row[client_idx].strip() else clientName
                acct_type = row[type_idx].strip() if type_idx != -1 and type_idx < len(row) else "Expense"
                sub_type = row[sub_type_idx].strip() if sub_type_idx != -1 and sub_type_idx < len(row) else ""
                level_val = int(row[level_idx].strip()) if level_idx != -1 and level_idx < len(row) and row[level_idx].strip().isdigit() else 0
                parent_val = row[parent_idx].strip() if parent_idx != -1 and parent_idx < len(row) and row[parent_idx].strip() else parentName
                
                new_id = str(uuid.uuid4())
                cur.execute('''
                    INSERT INTO "ClientChartOfAccounts" ("id", "clientName", "parentName", "accountNumber", "accountName", "type", "subType", "level", "createdAt", "updatedAt")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT ("clientName", "accountNumber")
                    DO UPDATE SET "parentName" = EXCLUDED."parentName", "accountName" = EXCLUDED."accountName", "type" = EXCLUDED."type", "subType" = EXCLUDED."subType", "level" = EXCLUDED."level", "updatedAt" = CURRENT_TIMESTAMP;
                ''', (new_id, client_val, parent_val, acct_num, acct_name, acct_type, sub_type, level_val))
                count += 1
            conn.commit()
            return {"success": True, "message": f"Successfully imported {count} accounts."}
    except Exception as e:
        print(f"Error uploading COA CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/clients/parent-mappings")
async def get_parent_mappings_endpoint(request: Request, parentName: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    resolved_parent = parentName or get_user_parent_name(username)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = 'SELECT id, "parentName", "clientName" FROM "ParentClientMap"'
            params = []
            if resolved_parent:
                query += ' WHERE LOWER("parentName") = LOWER(%s)'
                params.append(resolved_parent)
            query += ' ORDER BY "parentName" ASC, "clientName" ASC;'
            cur.execute(query, params)
            mappings = cur.fetchall() or []
            return {"success": True, "mappings": mappings}
    except Exception as e:
        print(f"Error fetching parent mappings: {e}")
        return {"success": False, "error": str(e), "mappings": []}
    finally:
        if conn: conn.close()

@app.post("/api/clients/parent-mappings")
async def save_parent_mapping_endpoint(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    body = await request.json()
    parent_name = (body.get("parentName") or get_user_parent_name(username)).strip()
    client_name = (body.get("clientName") or "").strip()
    if not parent_name or not client_name:
        raise HTTPException(status_code=400, detail="parentName and clientName are required.")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            import uuid
            new_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO "ParentClientMap" ("id", "parentName", "clientName", "createdAt", "updatedAt")
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT ("parentName", "clientName")
                DO UPDATE SET "updatedAt" = CURRENT_TIMESTAMP
                RETURNING *;
            ''', (new_id, parent_name, client_name))
            mapping = cur.fetchone()
            conn.commit()
            return {"success": True, "mapping": mapping}
    except Exception as e:
        print(f"Error saving parent mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.delete("/api/clients/parent-mappings")
async def delete_parent_mapping_endpoint(request: Request, id: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    if not id:
        raise HTTPException(status_code=400, detail="ID is required.")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('DELETE FROM "ParentClientMap" WHERE "id" = %s;', (id,))
            conn.commit()
            return {"success": True, "message": "Mapping deleted"}
    except Exception as e:
        print(f"Error deleting parent mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.get("/api/clients/history")
async def get_history_rules_endpoint(request: Request, clientName: str = "", parentName: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    resolved_parent = parentName or get_user_parent_name(username)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = 'SELECT id, "clientName", "parentName", "pattern", "description", "accountNumber", "accountName", "transactionType", "source", "confidenceScore", "useCount" FROM "ClientTransactionHistory"'
            conditions = []
            params = []
            if clientName:
                conditions.append('LOWER("clientName") = LOWER(%s)')
                params.append(clientName)
            if resolved_parent:
                conditions.append('LOWER("parentName") = LOWER(%s)')
                params.append(resolved_parent)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += ' ORDER BY "updatedAt" DESC;'
            cur.execute(query, params)
            historyRules = cur.fetchall() or []
            return {"success": True, "historyRules": historyRules}
    except Exception as e:
        print(f"Error fetching history rules: {e}")
        return {"success": False, "error": str(e), "historyRules": []}
    finally:
        if conn: conn.close()

@app.post("/api/clients/history")
@app.put("/api/clients/history")
async def save_history_rule_endpoint(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    body = await request.json()
    record_id = body.get("id")
    client_name = body.get("clientName") or "DEFAULT"
    parent_name = body.get("parentName") or get_user_parent_name(username)
    pattern = (body.get("pattern") or "").upper().strip()
    description = (body.get("description") or "").strip()
    account_number = (body.get("accountNumber") or "").strip()
    account_name = (body.get("accountName") or "").strip()
    tx_type = (body.get("transactionType") or "ALL").upper().strip()

    if not pattern or not account_number:
        raise HTTPException(status_code=400, detail="pattern and accountNumber are required.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if record_id:
                cur.execute('''
                    UPDATE "ClientTransactionHistory"
                    SET "parentName" = %s, "pattern" = %s, "description" = %s, "accountNumber" = %s, "accountName" = %s, "transactionType" = %s, "source" = 'MANUAL_EDIT', "updatedAt" = CURRENT_TIMESTAMP
                    WHERE "id" = %s
                    RETURNING *;
                ''', (parent_name, pattern, description, account_number, account_name, tx_type, record_id))
                rule = cur.fetchone()
            else:
                cur.execute('''
                    SELECT id FROM "ClientTransactionHistory"
                    WHERE "clientName" = %s AND "pattern" = %s AND "transactionType" = %s;
                ''', (client_name, pattern, tx_type))
                existing = cur.fetchone()
                if existing:
                    cur.execute('''
                        UPDATE "ClientTransactionHistory"
                        SET "parentName" = %s, "description" = %s, "accountNumber" = %s, "accountName" = %s, "source" = 'MANUAL_EDIT', "updatedAt" = CURRENT_TIMESTAMP
                        WHERE "id" = %s
                        RETURNING *;
                    ''', (parent_name, description, account_number, account_name, existing['id']))
                    rule = cur.fetchone()
                else:
                    import uuid
                    new_id = str(uuid.uuid4())
                    cur.execute('''
                        INSERT INTO "ClientTransactionHistory" ("id", "clientName", "parentName", "pattern", "description", "accountNumber", "accountName", "transactionType", "source", "confidenceScore", "useCount", "createdAt", "updatedAt")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'MANUAL_EDIT', 1.0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING *;
                    ''', (new_id, client_name, parent_name, pattern, description, account_number, account_name, tx_type))
                    rule = cur.fetchone()
            conn.commit()
            return {"success": True, "rule": rule}
    except Exception as e:
        print(f"Error saving history rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.delete("/api/clients/history")
async def delete_history_rule_endpoint(request: Request, id: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    if not id:
        raise HTTPException(status_code=400, detail="ID is required.")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "ClientTransactionHistory" WHERE "id" = %s;', (id,))
            conn.commit()
            return {"success": True, "message": "Rule deleted"}
    except Exception as e:
        print(f"Error deleting history rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@app.post("/api/clients/upload-history")
async def upload_history_rules_endpoint(request: Request, clientName: str = Form(...), parentName: str = Form("VRT Services"), file: UploadFile = File(...)):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing headers.")
    headers = [h.strip().replace('"', '') for h in lines[0].split(',')]
    
    import re
    pattern_idx = next((i for i, h in enumerate(headers) if re.search(r'pattern|vendor|keyword', h, re.I)), -1)
    if pattern_idx == -1:
        pattern_idx = next((i for i, h in enumerate(headers) if re.search(r'description', h, re.I)), -1)
    desc_idx = next((i for i, h in enumerate(headers) if re.search(r'description|memo|notes', h, re.I)), -1)
    acct_num_idx = next((i for i, h in enumerate(headers) if re.search(r'account\s*number|acct|gl|code', h, re.I)), -1)
    acct_name_idx = next((i for i, h in enumerate(headers) if re.search(r'account\s*name|category|drake', h, re.I)), -1)
    tx_type_idx = next((i for i, h in enumerate(headers) if re.search(r'type|transaction\s*type', h, re.I)), -1)
    parent_idx = next((i for i, h in enumerate(headers) if re.search(r'parent', h, re.I)), -1)

    if pattern_idx == -1 or acct_num_idx == -1:
        raise HTTPException(status_code=400, detail='CSV must contain "Pattern" and "Account Number" columns.')

    import csv, uuid
    def clean_raw_desc(desc):
        if not desc: return ""
        t = desc.upper().strip()
        t = re.sub(r'\b\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?\b', ' ', t)
        t = re.sub(r'\bCard\s*\d+\b', ' ', t, flags=re.I)
        t = re.sub(r'\b[A-Z0-9]{12,}\b', ' ', t)
        t = re.sub(r'X{3,}\d*', ' ', t)
        t = re.sub(r'#\s*\d+', ' ', t)
        t = re.sub(r'\b\d{3}[-\s]\d{3}[-\s]\d{4}\b', ' ', t)
        t = re.sub(r'\b(?:STORE|ST|NO|UNIT)\s*#?\d+\b', ' ', t, flags=re.I)
        fillers = [r'\bPURCHASE AUTHORIZED ON\b', r'\bPURCHASE RETURN AUTHORIZED ON\b', r'\bRECURRING PAYMENT AUTHORIZED ON\b', r'\bBUSINESS TO BUSINESS ACH DEBIT\b', r'\bPURCHASE AUTHORIZED\b', r'\bPURCHASE\b', r'\bCHECKCARD\b', r'\bDEPOSIT\b', r'\bWITHDRAWAL\b', r'\bPAYMENT\b', r'\bEPAYR\b', r'\bDEBITPMT\b', r'\bDES:\b', r'\bID:\b']
        for f in fillers:
            t = re.sub(f, ' ', t, flags=re.I)
        t = re.sub(r'[^A-Z0-9\s&\.\-]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t or desc.upper().strip()

    reader = csv.reader(lines[1:])
    conn = get_db_connection()
    count = 0
    try:
        with conn.cursor() as cur:
            for row in reader:
                if not row or len(row) <= max(pattern_idx, acct_num_idx):
                    continue
                raw_pattern = row[pattern_idx].strip()
                acct_num = row[acct_num_idx].strip()
                if not raw_pattern or not acct_num:
                    continue
                cleaned_pattern = clean_raw_desc(raw_pattern)
                description_val = row[desc_idx].strip() if desc_idx != -1 and desc_idx < len(row) else ""
                acct_name = row[acct_name_idx].strip() if acct_name_idx != -1 and acct_name_idx < len(row) else ""
                tx_type = row[tx_type_idx].strip().upper() if tx_type_idx != -1 and tx_type_idx < len(row) and row[tx_type_idx].strip() else "ALL"
                parent_val = row[parent_idx].strip() if parent_idx != -1 and parent_idx < len(row) and row[parent_idx].strip() else parentName

                cur.execute('''
                    SELECT id FROM "ClientTransactionHistory"
                    WHERE "clientName" = %s AND "pattern" = %s AND "transactionType" = %s;
                ''', (clientName, cleaned_pattern, tx_type))
                row_found = cur.fetchone()
                if row_found:
                    cur.execute('''
                        UPDATE "ClientTransactionHistory"
                        SET "parentName" = %s, "description" = %s, "accountNumber" = %s, "accountName" = %s, "source" = 'CSV_UPLOAD', "updatedAt" = CURRENT_TIMESTAMP
                        WHERE "id" = %s;
                    ''', (parent_val, description_val, acct_num, acct_name, row_found[0]))
                else:
                    new_id = str(uuid.uuid4())
                    cur.execute('''
                        INSERT INTO "ClientTransactionHistory" ("id", "clientName", "parentName", "pattern", "description", "accountNumber", "accountName", "transactionType", "source", "confidenceScore", "useCount", "createdAt", "updatedAt")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'CSV_UPLOAD', 1.0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                    ''', (new_id, clientName, parent_val, cleaned_pattern, description_val, acct_num, acct_name, tx_type))
                count += 1
            conn.commit()
            return {"success": True, "message": f"Successfully imported {count} history rules."}
    except Exception as e:
        print(f"Error uploading History CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/history/learn")
async def learn_history_rule_endpoint(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = await request.json()
    client_name = payload.get("client_name") or "DEFAULT"
    parent_name = payload.get("parent_name") or get_user_parent_name(username)
    pattern = payload.get("pattern") or ""
    description = payload.get("description") or ""
    account_number = payload.get("account_number") or ""
    account_name = payload.get("account_name") or ""
    tx_type = payload.get("transaction_type") or "ALL"
    
    if not pattern or not account_number:
        raise HTTPException(status_code=400, detail="Pattern and account_number are required.")
        
    ok = save_history_rule(client_name, pattern, account_number, account_name, tx_type, parent_name, description)
    return {"success": ok, "message": f"Rule learned for '{pattern}' -> {account_number}"}

@app.post("/process")
async def process_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_history: bool = Form(True),
    parent_name: str = Form(None),
):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Access denied: Your account is assigned to '{assigned_site}'.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    user_parent = parent_name or get_user_parent_name(username)

    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "input.pdf")
    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    try:
        result_data = run_extraction(
            pdf_path, 
            temp_dir, 
            create_csv=False, 
            use_history=use_history, 
            client_history_fetcher=get_client_history_rules,
            parent_name=user_parent
        )
        
        # Record usage if logged in as a ClientUser
        current_username = get_current_username(request)
        if current_username:
            import fitz
            try:
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                doc.close()
                record_user_usage(current_username, page_count)
            except Exception as ex:
                print(f"Error counting pages or recording usage: {ex}")
                
        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        return result_data
    except ValueError as ve:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/process-checks")
async def process_check_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_history: bool = Form(True),
    parent_name: str = Form(None),
    client_name: str = Form(None),
):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Access denied: Your account is assigned to '{assigned_site}'.")

    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Only PDF and image files (.png, .jpg, .jpeg) are supported.")

    user_parent = parent_name or get_user_parent_name(username)

    temp_dir = tempfile.mkdtemp()
    check_file_path = os.path.join(temp_dir, f"input_check{ext}")
    try:
        with open(check_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded check file: {e}")

    try:
        check_data = extract_check_images(
            check_file_path, 
            temp_dir, 
            use_history=use_history, 
            client_history_fetcher=get_client_history_rules, 
            parent_name=user_parent,
            client_name=client_name,
            original_filename=file.filename
        )

        # Record page/file scan usage for check image extraction
        if username:
            try:
                record_user_usage(username, 1)
            except Exception as ex:
                print(f"Error recording check extraction usage: {ex}")

        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        return check_data
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Check image extraction failed: {str(e)}")


# ── DigitalOcean Spaces → Direct Extraction Endpoints ────────────────────────

@app.post("/process-from-do")
async def process_pdf_from_do(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Download a bank statement PDF from DigitalOcean Spaces server-side and run extraction."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Access denied: Your account is assigned to '{assigned_site}'.")

    data = await request.json()
    s3_key   = (data.get("key") or "").strip()
    use_history = bool(data.get("use_history", True))
    customer_id = data.get("customer_id")

    if not s3_key:
        raise HTTPException(status_code=400, detail="key is required.")
    if not s3_key.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for bank statement extraction.")

    # Validate customer belongs to user's parent account
    user_parent = get_user_parent_name(username)
    if customer_id:
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
                cust = cur.fetchone()
                if not cust:
                    raise HTTPException(status_code=404, detail="Customer not found.")
                cust_parent = (cust.get("parent_name") or "").strip().lower()
                user_parent_clean = user_parent.lower()
                if cust_parent and cust_parent != user_parent_clean and cust_parent not in ("", "vrt services") and user_parent_clean not in ("", "vrt services"):
                    raise HTTPException(status_code=403, detail="Access denied: Customer does not belong to your account.")
                # Validate key is within this customer's root folder
                root_folder = cust.get("do_folder_path") or f"{sanitize_folder_name(cust['legal_name'])}/"
                if not s3_key.startswith(root_folder.rstrip("/")):
                    raise HTTPException(status_code=403, detail="Access denied: File is outside customer storage path.")
        finally:
            if conn:
                conn.close()

    client, err = get_s3_client()
    if not client:
        raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

    temp_dir = tempfile.mkdtemp()
    filename = os.path.basename(s3_key) or "input.pdf"
    pdf_path = os.path.join(temp_dir, filename)

    try:
        client.download_file(bucket, s3_key, pdf_path)
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to download file from storage: {e}")

    try:
        result_data = run_extraction(
            pdf_path,
            temp_dir,
            create_csv=False,
            use_history=use_history,
            client_history_fetcher=get_client_history_rules,
            parent_name=user_parent
        )

        if customer_id:
            detected_period = extract_period_from_key(s3_key)
            update_customer_checklist_milestone(customer_id, detected_period, "statement_received")
            update_customer_checklist_milestone(customer_id, detected_period, "extraction_done")
        # Record usage
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            record_user_usage(username, page_count)
        except Exception as ex:
            print(f"Error counting pages or recording usage: {ex}")

        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        return result_data
    except ValueError as ve:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/process-checks-from-do")
async def process_checks_from_do(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Download check image file(s) from DigitalOcean Spaces server-side and run check extraction."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Access denied: Your account is assigned to '{assigned_site}'.")

    data = await request.json()
    s3_keys     = data.get("keys") or []
    use_history = bool(data.get("use_history", True))
    client_name = (data.get("client_name") or "").strip() or None
    customer_id = data.get("customer_id")

    if not s3_keys:
        raise HTTPException(status_code=400, detail="keys (list) is required.")

    user_parent = get_user_parent_name(username)
    root_folder = None

    if customer_id:
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
                cust = cur.fetchone()
                if not cust:
                    raise HTTPException(status_code=404, detail="Customer not found.")
                cust_parent = (cust.get("parent_name") or "").strip().lower()
                user_parent_clean = user_parent.lower()
                if cust_parent and cust_parent != user_parent_clean and cust_parent not in ("", "vrt services") and user_parent_clean not in ("", "vrt services"):
                    raise HTTPException(status_code=403, detail="Access denied: Customer does not belong to your account.")
                root_folder = cust.get("do_folder_path") or f"{sanitize_folder_name(cust['legal_name'])}/"
                if not client_name:
                    client_name = cust.get("legal_name")
        finally:
            if conn:
                conn.close()

    allowed_exts = {".pdf", ".png", ".jpg", ".jpeg"}
    all_checks = []
    total_pages_scanned = 0

    s3_client, err = get_s3_client()
    if not s3_client:
        raise HTTPException(status_code=400, detail=f"S3 client not configured: {err}")

    bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET

    for s3_key in s3_keys:
        ext = os.path.splitext(s3_key.lower())[1]
        if ext not in allowed_exts:
            continue
        if root_folder and not s3_key.startswith(root_folder.rstrip("/")):
            continue  # silently skip keys outside root for safety

        temp_dir = tempfile.mkdtemp()
        filename = os.path.basename(s3_key) or f"check{ext}"
        check_path = os.path.join(temp_dir, filename)

        try:
            s3_client.download_file(bucket, s3_key, check_path)
        except Exception as e:
            cleanup_temp_dir(temp_dir)
            print(f"[DO] Failed to download check file {s3_key}: {e}")
            continue

        # Calculate pages/scans count for this check file
        page_count = 1
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(check_path)
                page_count = len(doc)
                doc.close()
            except Exception:
                page_count = 1

        total_pages_scanned += page_count

        try:
            check_data = extract_check_images(
                check_path,
                temp_dir,
                use_history=use_history,
                client_history_fetcher=get_client_history_rules,
                parent_name=user_parent,
                client_name=client_name,
                original_filename=filename
            )
            all_checks.extend(check_data.get("checks", []))
            background_tasks.add_task(cleanup_temp_dir, temp_dir)
        except Exception as e:
            cleanup_temp_dir(temp_dir)
            print(f"[DO] Check extraction failed for {s3_key}: {e}")

    if customer_id and s3_keys:
        try:
            detected_period = extract_period_from_key(s3_keys[0])
            update_customer_checklist_milestone(customer_id, detected_period, "checks_received")
            update_customer_checklist_milestone(customer_id, detected_period, "extraction_done")
        except Exception as ex_m:
            print(f"Error updating checklist milestone for checks: {ex_m}")

    # Record user usage for check images scanned
    if username and total_pages_scanned > 0:
        try:
            record_user_usage(username, total_pages_scanned)
        except Exception as ex:
            print(f"Error recording check extraction usage from DO: {ex}")

    return {"checks": all_checks, "count": len(all_checks)}

@app.post("/support")
async def support_submit(
    request: Request,
    message: str = Form(...),
    file: UploadFile = File(None)
):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    allowed, assigned_site = is_user_allowed_on_site(username, request)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Access denied: Your account is assigned to '{assigned_site}'.")

    resend_key = (
        os.environ.get("RESEND_API_KEY") or
        os.environ.get("RESEND_KEY") or
        os.environ.get("RESEND_API_TOKEN") or
        os.environ.get("RESEND_TOKEN")
    )
    if resend_key:
        resend_key = resend_key.strip().strip('\'"')
    if not resend_key or not resend_key.startswith("re_"):
        raise HTTPException(
            status_code=500,
            detail="Support email feature is not configured: Resend API Key is missing or invalid on the server. Please add your Resend API Key (e.g., RESEND_API_KEY) in Easypanel environment variables."
        )

    clean_from = get_resend_from_email()
    from_email = clean_from
        
    clean_to = get_resend_to_email()
    
    subject = "Support Request - Bank Statement OCR Extractor"
    
    current_user = get_current_username(request) or APP_USERNAME or "Anonymous User"
    html_content = f"""
    <h3>Support Request</h3>
    <p><strong>User:</strong> {current_user}</p>
    <p><strong>Message:</strong></p>
    <p>{message.replace(chr(10), '<br>')}</p>
    """
    
    attachments = []
    if file and file.filename:
        file_bytes = await file.read()
        if len(file_bytes) > 0:
            b64_content = base64.b64encode(file_bytes).decode('utf-8')
            attachments.append({
                "filename": file.filename,
                "content": b64_content
            })
            
    payload = {
        "from": f"CRM Support <{clean_from}>",
        "to": [clean_to],
        "subject": subject,
        "html": html_content
    }
    if attachments:
        payload["attachments"] = attachments
        
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            print(f"Resend email sent successfully: {res_body}")
            return {"status": "success", "message": "Support email sent successfully."}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"Failed to send email via Resend: Code {e.code}, Response: {err_body}")
        
        found_key = resend_key or ""
        masked_env = f"{found_key[:6]}...{found_key[-4:]}" if len(found_key) > 10 else found_key
        raise HTTPException(status_code=500, detail=f"Failed to send support email: {err_body}. Used Key: {masked_env}, From: {from_email}")
    except Exception as e:
        print(f"Error occurred while sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

# ── Workload Pending Tasks Endpoint ──────────────────────────────────────────────
@app.get("/api/dashboard/pending-tasks")
async def get_dashboard_pending_tasks(request: Request, parentName: str = ""):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_parent = get_user_parent_name(username) or "VRT Services"
    target_parent = parentName.strip() if parentName.strip() else user_parent

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fetch all active customers
            sql = "SELECT id, custumer_number, customer_type, legal_name, display_name, email, phone, status, parent_name FROM customer WHERE LOWER(status) = 'active'"
            params = []

            if target_parent:
                if target_parent.lower() == "vrt services":
                    sql += " AND (LOWER(COALESCE(parent_name, '')) = LOWER(%s) OR parent_name IS NULL OR parent_name = '')"
                    params.append(target_parent)
                else:
                    sql += " AND (LOWER(COALESCE(parent_name, '')) = LOWER(%s))"
                    params.append(target_parent)

            sql += " ORDER BY id DESC;"
            cur.execute(sql, tuple(params))
            cust_records = cur.fetchall() or []

            pending_items = []
            bk_pending_count = 0
            tax_pending_count = 0
            total_customers_with_pending = set()

            for cust in cust_records:
                cust_id = cust["id"]
                c_type = (cust.get("customer_type") or "Business").strip()
                is_individual = c_type.lower() == "individual"

                bk_slug, bk_label = get_in_process_period(cur, cust_id, "bookkeeping")
                tax_slug, tax_label = get_in_process_period(cur, cust_id, "tax")

                cur.execute("""
                    SELECT * FROM customer_task_checklist
                    WHERE customer_id = %s AND period = %s;
                """, (cust_id, bk_slug))
                bk_row = cur.fetchone() or {}

                cur.execute("""
                    SELECT * FROM customer_task_checklist
                    WHERE customer_id = %s AND period = %s;
                """, (cust_id, tax_slug))
                tax_row = cur.fetchone() or {}

                # Calculate Bookkeeping Steps (4 steps)
                bk_total = 4
                bk_completed = 0
                bk_missing = []

                if not is_individual:
                    if bk_row.get("bank_statement_received"): bk_completed += 1
                    else: bk_missing.append("Bank Statement Received")

                    if bk_row.get("check_images_received"): bk_completed += 1
                    else: bk_missing.append("Check Images Received")

                    if bk_row.get("extraction_ai_categorization_done"): bk_completed += 1
                    else: bk_missing.append("AI Categorization")

                    if bk_row.get("accountant_reviewed"): bk_completed += 1
                    else: bk_missing.append("Accountant Review")
                
                bk_percent = int((bk_completed / bk_total) * 100) if not is_individual else 100

                # Calculate Tax Steps (8 steps)
                tax_total = 8
                tax_completed = 0
                tax_missing = []

                if tax_row.get("tax_docs_requested"): tax_completed += 1
                else: tax_missing.append("Docs Requested")

                if tax_row.get("tax_docs_received"): tax_completed += 1
                else: tax_missing.append("Docs Received")

                if tax_row.get("tax_organizer"): tax_completed += 1
                else: tax_missing.append("Tax Organizer")

                if tax_row.get("tax_preparation"): tax_completed += 1
                else: tax_missing.append("Preparation")

                if tax_row.get("tax_review"): tax_completed += 1
                else: tax_missing.append("Review")

                if tax_row.get("tax_client_signature"): tax_completed += 1
                else: tax_missing.append("Client Signature")

                if tax_row.get("tax_efile"): tax_completed += 1
                else: tax_missing.append("E-file")

                if tax_row.get("tax_accepted"): tax_completed += 1
                else: tax_missing.append("Accepted")

                tax_percent = int((tax_completed / tax_total) * 100)

                prev_bk_slug_default, _ = get_in_process_period(None, None, "bookkeeping")
                prev_tax_slug_default, _ = get_in_process_period(None, None, "tax")

                has_bk_pending = (not is_individual) and (bk_slug <= prev_bk_slug_default) and (bk_completed < bk_total)
                has_tax_pending = (tax_slug <= prev_tax_slug_default) and (tax_completed < tax_total)

                if has_bk_pending: bk_pending_count += 1
                if has_tax_pending: tax_pending_count += 1

                if has_bk_pending or has_tax_pending:
                    total_customers_with_pending.add(cust_id)
                    pending_items.append({
                        "customer_id": cust_id,
                        "id": cust_id,
                        "custumer_number": cust.get("custumer_number"),
                        "legal_name": cust.get("legal_name"),
                        "display_name": cust.get("display_name"),
                        "email": cust.get("email") or "",
                        "phone": cust.get("phone") or "",
                        "customer_type": c_type,
                        "period": bk_slug,
                        "bk_period": bk_slug,
                        "tax_period": tax_slug,
                        "is_individual": is_individual,
                        "bk": {
                            "period_slug": bk_slug,
                            "period_label": bk_label,
                            "completed_count": bk_completed,
                            "total_count": bk_total,
                            "progress_percent": bk_percent,
                            "missing_steps": bk_missing,
                            "has_pending": has_bk_pending
                        },
                        "tax": {
                            "period_slug": tax_slug,
                            "period_label": tax_label,
                            "completed_count": tax_completed,
                            "total_count": tax_total,
                            "progress_percent": tax_percent,
                            "missing_steps": tax_missing,
                            "has_pending": has_tax_pending
                        }
                    })

            return {
                "summary": {
                    "pending_bookkeeping_count": bk_pending_count,
                    "pending_tax_count": tax_pending_count,
                    "total_incomplete_customers": len(total_customers_with_pending)
                },
                "pending_tasks": pending_items
            }
    except Exception as e:
        print(f"Error fetching pending tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# ── AI RAG Assistant Endpoint ──────────────────────────────────────────
@app.post("/api/chat")
async def chat_ai_assistant(request: Request):
    try:
        body = await request.json()
        user_message = (body.get("message") or "").strip()
        parent_name = (body.get("parent_name") or get_current_username(request) or "VRT Services").strip()
        customer_ref = (body.get("customer_ref") or "").strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message content is required.")

        # Extract reference code from message if present e.g. "cust-4059", "CUST-1001", "4059"
        m_ref = re.search(r'\b(?:CUST-)?(\d{3,6})\b', user_message, re.IGNORECASE)
        is_ref_lookup = False
        if not customer_ref and m_ref:
            msg_lower = user_message.lower()
            if "cust" in msg_lower or re.match(r'^\s*(?:check|status|my status|cust-?)?\s*\d{3,6}\s*$', msg_lower):
                customer_ref = m_ref.group(1)
                is_ref_lookup = True
        elif customer_ref:
            is_ref_lookup = True

        import rag_engine
        tenant_slug = rag_engine.get_tenant_slug(parent_name)

        status_info = None
        customer_ref_not_found = False
        searched_ref = None

        if customer_ref:
            searched_ref = f"CUST-{customer_ref}" if not str(customer_ref).upper().startswith("CUST-") else customer_ref

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if customer_ref:
                    status_info = rag_engine.get_customer_task_status(cur, customer_ref, parent_name)
                    if not status_info and is_ref_lookup:
                        customer_ref_not_found = True
        except Exception as e_db:
            print(f"[RAG DB NOTICE]: {e_db}")
        finally:
            if conn:
                conn.close()

        # Retrieve relevant passages from vector store / knowledge base
        passages = rag_engine.retrieve_relevant_passages(user_message, tenant_slug, top_k=3)

        # Synthesize response
        ai_reply = rag_engine.synthesize_ai_response(
            user_query=user_message,
            parent_name=parent_name,
            status_info=status_info,
            passages=passages,
            customer_ref_not_found=customer_ref_not_found,
            searched_ref=searched_ref
        )

        return {
            "success": True,
            "reply": ai_reply,
            "customer_ref": customer_ref,
            "status_info": status_info,
            "tenant": tenant_slug
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        print(f"[RAG CHAT ERROR]: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/list")
async def list_knowledge_docs(request: Request, parent_name: str = ""):
    import rag_engine
    tenant_slug = rag_engine.get_tenant_slug(parent_name or get_current_username(request) or "VRT Services")
    kb_base = rag_engine.KB_DIR

    all_flat_docs = []
    category_list = []

    available_slugs = []
    if os.path.exists(kb_base):
        for item in sorted(os.listdir(kb_base)):
            item_path = os.path.join(kb_base, item)
            if os.path.isdir(item_path):
                available_slugs.append(item)

    if tenant_slug not in available_slugs and available_slugs:
        available_slugs.insert(0, tenant_slug)

    for slug in available_slugs:
        cat_dir = os.path.join(kb_base, slug)
        cat_name = "VRT Services Knowledge" if slug == "vrt_services" else ("Datalazo LLC Knowledge" if slug == "datalazo_llc" else f"{slug.replace('_', ' ').title()} Knowledge")
        icon = "🏢" if slug == "vrt_services" else "💻"
        cat_items = []

        if os.path.exists(cat_dir):
            for file in sorted(os.listdir(cat_dir)):
                if file.endswith(".md") or file.endswith(".txt"):
                    rel_path = f"{slug}/{file}"
                    title = file.replace("_", " ").replace(".md", "").replace(".txt", "").title()
                    doc_obj = {
                        "filename": file,
                        "rel_path": rel_path,
                        "path": rel_path,
                        "title": title,
                        "tenant_slug": slug
                    }
                    cat_items.append(doc_obj)
                    all_flat_docs.append(doc_obj)

        category_list.append({
            "category": cat_name,
            "slug": slug,
            "icon": icon,
            "items": cat_items
        })

    return {
        "success": True,
        "tenant": tenant_slug,
        "docs": all_flat_docs,
        "categories": category_list
    }

@app.get("/api/knowledge/doc")
async def get_knowledge_doc(request: Request, path: str = ""):
    import rag_engine
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    full_path = os.path.join(rag_engine.KB_DIR, path.replace("/", os.sep))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return {"success": True, "path": path, "content": content}

@app.post("/api/knowledge/save")
async def save_knowledge_doc(request: Request):
    import rag_engine
    body = await request.json()
    rel_path = (body.get("path") or "").strip()
    content = body.get("content") or ""
    parent_name = (body.get("parent_name") or get_current_username(request) or "VRT Services").strip()
    tenant_slug = rag_engine.get_tenant_slug(parent_name)

    if not rel_path or ".." in rel_path:
        raise HTTPException(status_code=400, detail="Invalid document path.")
    
    # Enforce strict tenant isolation
    target_cat = rel_path.split("/")[0] if "/" in rel_path else rel_path
    if target_cat != tenant_slug:
        raise HTTPException(status_code=403, detail="Access denied: Cannot edit documents belonging to another organization.")

    full_path = os.path.join(rag_engine.KB_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return {"success": True, "message": "Article saved successfully.", "path": rel_path}

@app.post("/api/knowledge/create")
async def create_knowledge_doc(request: Request):
    import rag_engine
    body = await request.json()
    parent_name = (body.get("parent_name") or get_current_username(request) or "VRT Services").strip()
    tenant_slug = rag_engine.get_tenant_slug(parent_name)
    category_slug = tenant_slug
    
    title = (body.get("title") or "").strip()
    content = body.get("content") or f"# {title}\n\nWrite article content here..."
    
    if not title:
        raise HTTPException(status_code=400, detail="Title is required.")
    
    filename = re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower()).strip('_') + ".md"
    rel_path = f"{category_slug}/{filename}"
    full_path = os.path.join(rag_engine.KB_DIR, rel_path.replace("/", os.sep))
    
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return {"success": True, "message": "New article created successfully.", "path": rel_path, "filename": filename}

@app.delete("/api/knowledge/delete")
async def delete_knowledge_doc(request: Request, path: str = "", parent_name: str = ""):
    import rag_engine
    tenant_slug = rag_engine.get_tenant_slug(parent_name or get_current_username(request) or "VRT Services")
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path.")
    
    target_cat = path.split("/")[0] if "/" in path else path
    if target_cat != tenant_slug:
        raise HTTPException(status_code=403, detail="Access denied: Cannot delete documents belonging to another organization.")

    full_path = os.path.join(rag_engine.KB_DIR, path.replace("/", os.sep))
    if os.path.exists(full_path):
        os.remove(full_path)
        return {"success": True, "message": "Article deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail="File not found.")

@app.post("/api/knowledge/upload")
async def upload_knowledge_doc(
    request: Request,
    file: UploadFile = File(...),
    parent_name: str = Form("")
):
    import rag_engine, zipfile, io, xml.etree.ElementTree as ET
    tenant_slug = rag_engine.get_tenant_slug(parent_name or get_current_username(request) or "VRT Services")
    
    filename = file.filename or "uploaded_doc"
    ext = os.path.splitext(filename)[1].lower()
    content_bytes = await file.read()
    
    extracted_text = ""
    
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            pages = []
            for idx, page in enumerate(doc):
                p_text = page.get_text()
                if p_text.strip():
                    pages.append(f"## Page {idx + 1}\n\n{p_text.strip()}")
            extracted_text = "\n\n".join(pages)
        except Exception as pe:
            print(f"[PDF Extract Error]: {pe}")
            extracted_text = content_bytes.decode("utf-8", errors="ignore")
    elif ext in [".docx", ".doc"]:
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                paragraphs = []
                for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                extracted_text = "\n\n".join(paragraphs)
        except Exception as de:
            print(f"[DOCX Extract Error]: {de}")
            extracted_text = content_bytes.decode("utf-8", errors="ignore")
    else:
        extracted_text = content_bytes.decode("utf-8", errors="ignore")

    clean_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
    if not extracted_text.strip().startswith("#"):
        final_markdown = f"# {clean_title}\n\n{extracted_text.strip()}"
    else:
        final_markdown = extracted_text.strip()

    safe_base = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(filename)[0].lower()).strip('_')
    md_filename = f"{safe_base}.md"
    rel_path = f"{tenant_slug}/{md_filename}"
    full_path = os.path.join(rag_engine.KB_DIR, rel_path.replace("/", os.sep))

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(final_markdown)

    return {
        "success": True,
        "filename": filename,
        "md_filename": md_filename,
        "path": rel_path,
        "title": clean_title,
        "message": f"Successfully processed '{filename}' into Knowledge Base article!"
    }

# ── Customer Email Communication & Inbound Webhooks ───────────────────────────
@app.post("/api/customers/{customer_id}/send-email")
async def send_customer_email(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    subject = (body.get("subject") or "").strip()
    message_text = (body.get("message") or "").strip()
    default_reply_to = get_resend_reply_to_email()
    custom_reply_to = (body.get("reply_to") or "").strip()
    if not custom_reply_to or "@" not in custom_reply_to or "receive.datalazo.net" in custom_reply_to.lower():
        custom_reply_to = default_reply_to

    if not subject or not message_text:
        raise HTTPException(status_code=400, detail="Subject and message text are required.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM customer WHERE id = %s;", (customer_id,))
            cust = cur.fetchone()
            if not cust:
                raise HTTPException(status_code=404, detail="Customer not found")

        recipient_email = parse_clean_email(body.get("recipient_email") or body.get("to") or cust.get("email") or "")
        if not recipient_email:
            raise HTTPException(status_code=400, detail=f"Customer '{cust['legal_name']}' does not have a valid email address configured.")

        if recipient_email and parse_clean_email(cust.get("email") or "") != recipient_email:
            with conn.cursor() as cur:
                cur.execute("UPDATE customer SET email = %s WHERE id = %s;", (recipient_email, customer_id))
                conn.commit()
            cust["email"] = recipient_email

        reply_to_list = parse_reply_to_list(custom_reply_to or default_reply_to)
        clean_reply_to = ", ".join(reply_to_list)
        reply_to_payload = reply_to_list if len(reply_to_list) > 1 else reply_to_list[0]

        parent_name = (cust.get("parent_name") or get_user_parent_name(username) or "VRT Services").strip()
        sender_display_name = f"{parent_name} Portal" if "Portal" not in parent_name else parent_name
        raw_ref = str(cust.get('custumer_number') or cust['id']).strip()
        cust_ref = raw_ref if raw_ref.upper().startswith("CUST-") else f"CUST-{raw_ref}"
        ref_tag = f"[Ref: {cust_ref}]"
        full_subject = subject if ref_tag.lower() in subject.lower() else f"{subject} {ref_tag}"

        # HTML formatted message
        formatted_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <div style="border-bottom: 2px solid #7f00ff; padding-bottom: 12px; margin-bottom: 20px;">
                <h2 style="color: #0b0c10; margin: 0; font-size: 1.25rem;">{cust['legal_name']}</h2>
                <p style="color: #64748b; margin: 4px 0 0 0; font-size: 0.85rem;">Communication Message</p>
            </div>
            <div style="white-space: pre-wrap; font-size: 0.95rem; color: #1e293b;">{message_text}</div>
            <div style="margin-top: 30px; padding-top: 14px; border-top: 1px solid #cbd5e1; font-size: 0.78rem; color: #64748b;">
                <p style="margin: 0;">Sent via {sender_display_name}. Please reply to this email directly to send files or responses to your account team.</p>
                <p style="margin: 4px 0 0 0; font-family: monospace; color: #94a3b8;">Ref: {cust_ref}</p>
            </div>
        </div>
        """

        # Resend API credentials
        resend_key = (
            os.environ.get("RESEND_API_KEY") or
            os.environ.get("RESEND_KEY") or
            os.environ.get("RESEND_API_TOKEN") or
            os.environ.get("RESEND_TOKEN")
        )
        if resend_key:
            resend_key = resend_key.strip().strip('\'"')
        clean_from = get_resend_from_email()
        from_email = clean_from

        if not resend_key:
            raise HTTPException(status_code=500, detail="RESEND_API_KEY is not configured in environment variables.")

        payload = {
            "from": format_resend_from_header(sender_display_name),
            "to": [recipient_email],
            "reply_to": reply_to_payload,
            "subject": full_subject,
            "html": formatted_html,
            "text": message_text
        }

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {resend_key.strip()}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print(f"[EMAIL SENT] Customer {customer_id} ({recipient_email}): {res_body}")

        # Log outbound communication in database
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO customer_communications (
                    customer_id, direction, sender_email, recipient_email, reply_to_email,
                    subject, body_text, status, created_at
                ) VALUES (
                    %s, 'OUTBOUND', %s, %s, %s, %s, %s, 'DELIVERED', CURRENT_TIMESTAMP
                );
            """, (customer_id, from_email, recipient_email, custom_reply_to, full_subject, message_text))
            conn.commit()

        return {
            "success": True,
            "message": f"Email sent successfully to {recipient_email}",
            "reply_to": custom_reply_to,
            "subject": full_subject
        }
    except HTTPException as he:
        raise he
    except urllib.error.HTTPError as he_err:
        err_text = he_err.read().decode("utf-8")
        print(f"Resend HTTP Error: {err_text}")
        if "not verified" in err_text.lower():
            err_text += " (Note: To send without domain verification, use 'vrt@ostooechei.resend.app' as Reply-To, or add & verify your custom domain at https://resend.com/domains)"
        raise HTTPException(status_code=500, detail=f"Resend Email API error: {err_text}")
    except Exception as e:
        print(f"Error sending email to customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/customers/{customer_id}/communications")
async def get_customer_communications(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM customer_communications
                WHERE customer_id = %s
                ORDER BY created_at DESC;
            """, (customer_id,))
            records = cur.fetchall()

            history = []
            for r in records:
                row = dict(r)
                if row.get("created_at"):
                    val = row["created_at"]
                    if isinstance(val, datetime.datetime) and val.tzinfo is None:
                        val = val.replace(tzinfo=datetime.timezone.utc)
                    row["created_at"] = val.isoformat() if hasattr(val, "isoformat") else str(val)
                if row.get("read_at"):
                    val = row["read_at"]
                    if isinstance(val, datetime.datetime) and val.tzinfo is None:
                        val = val.replace(tzinfo=datetime.timezone.utc)
                    row["read_at"] = val.isoformat() if hasattr(val, "isoformat") else str(val)
                history.append(row)

            return {"communications": history}
    except Exception as e:
        print(f"Error fetching communications history for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/customers/{customer_id}/communications/mark-read")
async def mark_customer_communications_read(customer_id: int, request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE customer_communications
                SET is_read = TRUE, status = 'READ', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                WHERE customer_id = %s AND direction = 'INBOUND';
            """, (customer_id,))
            conn.commit()
        return {"success": True}
    except Exception as e:
        print(f"Error marking communications read for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/api/communications/{comm_id}/mark-single-read")
async def mark_single_communication_read(comm_id: int, request: Request):
    """Marks a single inbound communication record as read with timestamp."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE customer_communications
                SET is_read = TRUE, status = 'READ', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                WHERE id = %s AND direction = 'INBOUND'
                RETURNING id, customer_id, read_at;
            """, (comm_id,))
            updated = cur.fetchone()
            conn.commit()
            if not updated:
                return {"success": False, "message": "Communication not found or already read"}
            
            read_at_val = updated.get("read_at")
            if isinstance(read_at_val, datetime.datetime) and read_at_val.tzinfo is None:
                read_at_val = read_at_val.replace(tzinfo=datetime.timezone.utc)
            read_at_str = read_at_val.isoformat() if hasattr(read_at_val, "isoformat") else (str(read_at_val) if read_at_val else None)
            return {
                "success": True, 
                "comm_id": comm_id, 
                "customer_id": updated["customer_id"], 
                "read_at": read_at_str
            }
    except Exception as e:
        print(f"Error marking communication {comm_id} read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/communications/recent")
async def get_recent_inbound_communications(request: Request):
    """Returns the last 30 inbound customer communications across all customers for the active organization."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_parent = get_user_parent_name(username) or "VRT Services"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_parent.lower() == "vrt services":
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.parent_name IS NULL OR cust.parent_name = '' OR cust.custumer_number = 'CUST-0000')"
            else:
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.custumer_number = 'CUST-0000')"

            cur.execute(f"""
                SELECT c.*, cust.legal_name, cust.custumer_number
                FROM customer_communications c
                JOIN customer cust ON c.customer_id = cust.id
                WHERE c.direction = 'INBOUND' AND {parent_filter}
                ORDER BY c.created_at DESC
                LIMIT 30;
            """, (user_parent,))
            records = cur.fetchall()

            history = []
            for r in records:
                row = dict(r)
                if row.get("created_at"):
                    val = row["created_at"]
                    if isinstance(val, datetime.datetime) and val.tzinfo is None:
                        val = val.replace(tzinfo=datetime.timezone.utc)
                    row["created_at"] = val.isoformat() if hasattr(val, "isoformat") else str(val)
                if row.get("read_at"):
                    val = row["read_at"]
                    if isinstance(val, datetime.datetime) and val.tzinfo is None:
                        val = val.replace(tzinfo=datetime.timezone.utc)
                    row["read_at"] = val.isoformat() if hasattr(val, "isoformat") else str(val)
                history.append(row)

            return {"communications": history}
    except Exception as e:
        print(f"Error fetching recent communications: {e}")
        return {"communications": []}
    finally:
        if conn:
            conn.close()

@app.get("/api/communications/unread-summary")
async def get_unread_communications_summary(request: Request):
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_parent = get_user_parent_name(username) or "VRT Services"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_parent.lower() == "vrt services":
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.parent_name IS NULL OR cust.parent_name = '' OR cust.custumer_number = 'CUST-0000')"
            else:
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.custumer_number = 'CUST-0000')"

            cur.execute(f"""
                SELECT c.customer_id, cust.legal_name, COUNT(*) as unread_count
                FROM customer_communications c
                JOIN customer cust ON c.customer_id = cust.id
                WHERE c.direction = 'INBOUND' AND (c.is_read = FALSE OR c.is_read IS NULL)
                AND {parent_filter}
                GROUP BY c.customer_id, cust.legal_name;
            """, (user_parent,))
            rows = cur.fetchall()
            unread_map = {r["customer_id"]: r for r in rows}
            total_unread = sum(r["unread_count"] for r in rows)
            return {"total_unread": total_unread, "unread_by_customer": unread_map}
    except Exception as e:
        print(f"Error fetching unread communications summary: {e}")
        return {"total_unread": 0, "unread_by_customer": {}}
    finally:
        if conn:
            conn.close()

@app.post("/api/communications/mark-all-read")
async def mark_all_communications_read(request: Request):
    """Marks all inbound unread communication records as read for the active organization."""
    username = get_current_username(request)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_parent = get_user_parent_name(username) or "VRT Services"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if user_parent.lower() == "vrt services":
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.parent_name IS NULL OR cust.parent_name = '' OR cust.custumer_number = 'CUST-0000')"
            else:
                parent_filter = "(LOWER(COALESCE(cust.parent_name, '')) = LOWER(%s) OR cust.custumer_number = 'CUST-0000')"

            cur.execute(f"""
                UPDATE customer_communications
                SET is_read = TRUE, status = 'READ', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                FROM customer cust
                WHERE customer_communications.customer_id = cust.id
                AND customer_communications.direction = 'INBOUND' 
                AND (customer_communications.is_read = FALSE OR customer_communications.is_read IS NULL)
                AND {parent_filter};
            """, (user_parent,))
            conn.commit()
        return {"success": True, "message": "All unread messages marked as read."}
    except Exception as e:
        print(f"Error marking all communications read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

LAST_INBOUND_DEBUG = {}

BUILD_VERSION = "v40-fix-fresh-main-conn-webhook"

@app.get("/api/version")
async def get_version():
    """Public endpoint — returns the version tag and git commit hash of the running server."""
    import subprocess, os
    commit = BUILD_VERSION
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.abspath(__file__)) or ".", stderr=subprocess.DEVNULL).decode().strip()
        if git_hash:
            commit = f"{git_hash} ({BUILD_VERSION})"
    except Exception:
        pass
    return {"git_commit": commit, "build_version": BUILD_VERSION, "status": "active"}

@app.get("/api/debug/inbound-status")
async def get_inbound_status_public():
    """Public diagnostic: checks CUST-0000 existence, last 5 webhook logs, last 5 INBOUND communications."""

    result = {}
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Check CUST-0000 exists
            cur.execute("SELECT id, custumer_number, legal_name, status FROM customer WHERE custumer_number = 'CUST-0000';")
            cust0 = cur.fetchone()
            result["cust_0000"] = dict(cust0) if cust0 else None
            cust0_id = cust0["id"] if cust0 else None

            # 2. Last 10 webhook debug log entries (all statuses)
            cur.execute("""
                SELECT id, sender_email, recipient_email, subject, customer_id, status, payload_json, created_at
                FROM webhook_debug_log ORDER BY id DESC LIMIT 10;
            """)
            result["last_webhook_logs"] = [dict(r) | {"created_at": str(r["created_at"])} for r in cur.fetchall()]

            # 3. Last 5 communications overall
            cur.execute("""
                SELECT id, customer_id, sender_email, recipient_email, subject, direction, is_read, created_at
                FROM customer_communications ORDER BY id DESC LIMIT 5;
            """)
            result["last_comms_overall"] = [dict(r) | {"created_at": str(r["created_at"])} for r in cur.fetchall()]

            # 4. CUST-0000 specific communications (unlinked inbound emails)
            if cust0_id:
                cur.execute("""
                    SELECT id, customer_id, sender_email, recipient_email, subject, direction, is_read, created_at
                    FROM customer_communications WHERE customer_id = %s ORDER BY id DESC LIMIT 10;
                """, (cust0_id,))
                rows = cur.fetchall()
                result["cust_0000_comms"] = [dict(r) | {"created_at": str(r["created_at"])} for r in rows]
                result["cust_0000_comms_count"] = len(rows)
            else:
                result["cust_0000_comms"] = []
                result["cust_0000_comms_count"] = 0

            # 5. All customer email mappings
            cur.execute("SELECT id, custumer_number, legal_name, email FROM customer ORDER BY id ASC;")
            result["all_customers"] = [dict(r) for r in cur.fetchall()]
            result["total_customers"] = len(result["all_customers"])

            # 6. Last 15 communications overall
            cur.execute("""
                SELECT id, customer_id, sender_email, recipient_email, subject, direction, is_read, created_at
                FROM customer_communications ORDER BY id DESC LIMIT 15;
            """, ())
            result["last_15_comms"] = [dict(r) | {"created_at": str(r["created_at"])} for r in cur.fetchall()]

            # 7. Webhook processing summary (RECEIVED vs SUCCESS vs ERROR in last 24h)
            cur.execute("""
                SELECT status, COUNT(*) as cnt FROM webhook_debug_log
                WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
                GROUP BY status ORDER BY cnt DESC;
            """)
            result["webhook_status_summary_24h"] = [dict(r) for r in cur.fetchall()]

    except Exception as e:
        result["error"] = str(e)
    finally:
        if conn:
            conn.close()
    return result


@app.get("/api/debug/full-trace")
async def get_full_trace_public():
    """Public diagnostic endpoint — trace all customers, last 20 webhooks, and last 20 communications."""
    trace = {}
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, custumer_number, legal_name, display_name, email, parent_name, status FROM customer ORDER BY id ASC;")
            trace["customers"] = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT id, sender_email, recipient_email, subject, customer_id, status, created_at FROM webhook_debug_log ORDER BY id DESC LIMIT 20;")
            trace["webhook_logs"] = [dict(r) | {"created_at": str(r["created_at"])} for r in cur.fetchall()]

            cur.execute("""
                SELECT c.id, c.customer_id, cust.custumer_number, cust.legal_name, c.sender_email, c.recipient_email, c.subject, c.direction, c.is_read, c.created_at
                FROM customer_communications c
                LEFT JOIN customer cust ON c.customer_id = cust.id
                ORDER BY c.id DESC LIMIT 20;
            """)
            trace["communications"] = [dict(r) | {"created_at": str(r["created_at"])} for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        trace["error"] = str(e)
    return trace


@app.get("/api/debug/last-inbound")
async def get_last_inbound_debug():
    """Diagnostic endpoint to inspect raw payload and extraction of last received webhooks and communications."""
    debug_info = {}
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Fetch from webhook_debug_log
            try:
                cur.execute("SELECT * FROM webhook_debug_log ORDER BY id DESC LIMIT 5;")
                rows = cur.fetchall()
                if rows:
                    logs = []
                    for r in rows:
                        row = dict(r)
                        if row.get("created_at"):
                            row["created_at"] = str(row["created_at"])
                        try:
                            if row.get("payload_json"):
                                row["payload_json"] = json.loads(row["payload_json"])
                        except Exception:
                            pass
                        logs.append(row)
                    debug_info["last_webhook_logs"] = logs
            except Exception as e_w:
                debug_info["webhook_log_err"] = str(e_w)

            # 2. Fetch last 5 INBOUND records from customer_communications
            try:
                cur.execute("""
                    SELECT id, customer_id, sender_email, recipient_email, subject, body_text, attachments_json, status, created_at 
                    FROM customer_communications 
                    WHERE direction = 'INBOUND' 
                    ORDER BY id DESC LIMIT 5;
                """)
                comm_rows = cur.fetchall()
                if comm_rows:
                    comms = []
                    for r in comm_rows:
                        row = dict(r)
                        if row.get("created_at"):
                            row["created_at"] = str(row["created_at"])
                        comms.append(row)
                    debug_info["last_inbound_communications"] = comms
            except Exception as e_c:
                debug_info["comm_fetch_err"] = str(e_c)

        conn.close()
    except Exception as e:
        print(f"Error in debug endpoint: {e}")
        debug_info["endpoint_err"] = str(e)

    if not debug_info:
        debug_info = {"status": "No webhooks or inbound communications recorded yet in DB."}
    return debug_info

@app.get("/api/debug/test-resend-fetch")
async def test_resend_fetch_debug():
    """Live diagnostic endpoint to test Resend API key & fetch responses for recent emails."""
    resend_key = (
        os.environ.get("RESEND_API_KEY") or 
        os.environ.get("RESEND_KEY") or 
        os.environ.get("RESEND_TOKEN") or 
        ""
    ).strip()
    
    result = {
        "resend_key_configured": bool(resend_key),
        "resend_key_prefix": (resend_key[:6] + "...") if resend_key else "NONE",
        "resend_api_list": {},
        "api_responses": {}
    }
    
    if not resend_key:
        result["error"] = "RESEND_API_KEY environment variable is not configured on the server."
        return result

    # 1. Query Resend API list emails
    try:
        list_req = urllib.request.Request(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="GET"
        )
        with urllib.request.urlopen(list_req) as list_resp:
            list_text = list_resp.read().decode("utf-8")
            result["resend_api_list"] = json.loads(list_text)
    except urllib.error.HTTPError as he:
        result["resend_api_list"] = f"HTTP {he.code}: {he.reason}"
    except Exception as ex:
        result["resend_api_list"] = f"Error: {str(ex)}"

    # 2. Extract IDs from DB logs & API list
    email_ids = []
    if isinstance(result["resend_api_list"], dict) and isinstance(result["resend_api_list"].get("data"), list):
        for item in result["resend_api_list"]["data"]:
            if isinstance(item, dict) and item.get("id"):
                email_ids.append(item["id"])

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT payload_json FROM webhook_debug_log ORDER BY id DESC LIMIT 5;")
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                try:
                    payload = json.loads(r["payload_json"])
                    if isinstance(payload, dict):
                        d = payload.get("data") if isinstance(payload.get("data"), dict) else payload
                        eid = d.get("email_id") or d.get("id")
                        if eid and eid not in email_ids:
                            email_ids.append(eid)
                except Exception:
                    pass
    except Exception as e_db:
        result["db_error"] = str(e_db)

    result["found_email_ids"] = email_ids

    # 3. Query individual email endpoints for found IDs
    for eid in email_ids[:3]:
        for endpoint_url in [
            f"https://api.resend.com/emails/receiving/{eid}",
            f"https://api.resend.com/emails/{eid}"
        ]:
            try:
                req = urllib.request.Request(
                    endpoint_url,
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    method="GET"
                )
                with urllib.request.urlopen(req) as resp:
                    res_text = resp.read().decode("utf-8")
                    result["api_responses"][endpoint_url] = json.loads(res_text)
            except urllib.error.HTTPError as he:
                result["api_responses"][endpoint_url] = f"HTTP {he.code}: {he.reason}"
            except Exception as ex:
                result["api_responses"][endpoint_url] = f"Error: {str(ex)}"

    return result

def extract_attachments_from_mime(raw_mime_str: str) -> list:
    """Extract all attached files (filename, bytes) directly from a raw RFC-822 MIME email string."""
    attachments_found = []
    if not raw_mime_str or not isinstance(raw_mime_str, str) or len(raw_mime_str) < 20:
        return attachments_found
    try:
        import email as _email_mod
        msg = _email_mod.message_from_string(raw_mime_str)
        if msg.is_multipart():
            for part in msg.walk():
                cdisp = str(part.get('Content-Disposition') or '')
                filename = part.get_filename()
                if not filename and 'attachment' in cdisp.lower():
                    filename = "attached_file.pdf"
                if filename:
                    import html as _html_lib
                    clean_fn = _html_lib.unescape(filename).strip('"\' \t\r\n')
                    clean_fn = os.path.basename(clean_fn)
                    payload_bytes = part.get_payload(decode=True)
                    if payload_bytes and len(payload_bytes) > 0:
                        attachments_found.append({
                            "filename": clean_fn,
                            "bytes": payload_bytes
                        })
                        print(f"[MIME ATTACHMENT EXTRACTED]: '{clean_fn}' ({len(payload_bytes)} bytes)")
    except Exception as e_mime_att:
        print(f"[MIME ATTACHMENT EXTRACTION ERROR]: {e_mime_att}")
def download_resend_attachment(email_id: str, att_id: str, att_name: str, resend_key: str) -> bytes:
    """Attempt downloading attachment binary bytes from all Resend API endpoints."""
    if not resend_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {resend_key.strip()}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    identifiers = [att_id, att_name]
    for ident in identifiers:
        if not ident:
            continue
        
        urls_to_try = [
            f"https://api.resend.com/emails/receiving/{email_id}/attachments/{ident}",
            f"https://api.resend.com/emails/receiving/{email_id}/attachments/{ident}/download",
            f"https://api.resend.com/emails/{email_id}/attachments/{ident}",
            f"https://api.resend.com/emails/{email_id}/attachments/{ident}/download",
            f"https://api.resend.com/attachments/{ident}",
            f"https://api.resend.com/attachments/{ident}/download",
            f"https://api.resend.com/emails/inbound/{email_id}/attachments/{ident}"
        ]

        for target_url in urls_to_try:
            try:
                req = urllib.request.Request(target_url, headers=headers, method="GET")
                with urllib.request.urlopen(req) as resp:
                    raw_resp = resp.read()
                    if raw_resp and len(raw_resp) > 0:
                        return raw_resp
            except Exception as e_try:
                print(f"[RESEND ATTACHMENT FETCH NOTICE] {target_url}: {e_try}")
    return None

def process_inbound_post_processing(
    email_id: str,
    comm_id: int,
    customer_id: int,
    legal_name: str,
    parent_name: str,
    subject: str,
    sender_email: str,
    body_text: str,
    raw_body: dict,
    data: dict,
    attachments: list
):
    """Background worker task to fetch full body text, upload attachments to S3, and dispatch team alert emails asynchronously without delaying the webhook response."""
    # 1. Fetch full email body from Resend API if body_text is empty or short
    if email_id and (not body_text or len(body_text.strip()) == 0):
        _res_key = (os.environ.get("RESEND_API_KEY") or os.environ.get("RESEND_KEY") or os.environ.get("RESEND_TOKEN") or "").strip()
        if _res_key:
            for _endpoint in [
                f"https://api.resend.com/emails/{email_id}",
                f"https://api.resend.com/emails/receiving/{email_id}"
            ]:
                try:
                    _req_f = urllib.request.Request(
                        _endpoint,
                        headers={"Authorization": f"Bearer {_res_key}", "User-Agent": "Mozilla/5.0"},
                        method="GET"
                    )
                    with urllib.request.urlopen(_req_f, timeout=5) as _resp_f:
                        _f_json = json.loads(_resp_f.read().decode("utf-8"))
                        if isinstance(_f_json, dict):
                            _f_html = _f_json.get("html") or ""
                            _f_text = _f_json.get("text") or ""
                            def clean_html_to_text_local(html_str: str) -> str:
                                if not html_str or not isinstance(html_str, str): return ""
                                import html as _html_lib
                                text = re.sub(r'<(?:br|p|div|tr|h\d|li)[^>]*>', '\n', html_str, flags=re.IGNORECASE)
                                text = re.sub(r'<[^>]+>', '', text)
                                text = _html_lib.unescape(text)
                                text = re.sub(r'\n\s*\n', '\n\n', text).strip()
                                return text
                            _f_body = _f_text if _f_text and isinstance(_f_text, str) and len(_f_text.strip()) > 0 else clean_html_to_text_local(_f_html)
                            if _f_body and isinstance(_f_body, str) and len(_f_body.strip()) > 0:
                                body_text = _f_body.strip()
                                if comm_id:
                                    try:
                                        upd_conn = get_db_connection()
                                        with upd_conn.cursor() as cur:
                                            cur.execute("UPDATE customer_communications SET body_text = %s WHERE id = %s;", (body_text, comm_id))
                                            upd_conn.commit()
                                        upd_conn.close()
                                    except Exception as e_upd_body:
                                        print(f"[ASYNC BODY UPDATE ERROR]: {e_upd_body}")
                                break
                except Exception as _e_f:
                    print(f"[ASYNC RESEND BODY FETCH NOTICE] {_endpoint}: {_e_f}")

    # 2. Process S3 attachments
    saved_attachments = []
    try:
        mime_att_list = []
        for obj in [data, raw_body]:
            if isinstance(obj, dict):
                raw_mime = obj.get("raw") or obj.get("mime") or obj.get("raw_email") or obj.get("email_raw")
                if raw_mime and isinstance(raw_mime, str) and len(raw_mime) > 20:
                    mime_att_list = extract_attachments_from_mime(raw_mime)
                    if mime_att_list:
                        break

        _att_list = attachments if (isinstance(attachments, list)) else []
        _resend_key = os.environ.get("RESEND_API_KEY") or ""

        if mime_att_list or _att_list:
            s3client, s3err = get_s3_client()
            if s3client:
                bucket = os.environ.get("DO_SPACES_BUCKET") or DO_SPACES_BUCKET
                _s3_parent = sanitize_folder_name(parent_name or "VRT Services")
                _s3_legal  = sanitize_folder_name(legal_name or "Unknown")
                target_folder = f"{_s3_parent}/{_s3_legal}/Inbox/"

                for m_att in mime_att_list:
                    m_name  = m_att.get("filename") or "attached_file.pdf"
                    m_bytes = m_att.get("bytes")
                    if m_bytes:
                        fk = f"{target_folder}{m_name}"
                        s3client.put_object(Bucket=bucket, Key=fk, Body=m_bytes, ACL='private')
                        saved_attachments.append(fk)

                for att in _att_list:
                    file_bytes, att_name, att_id = None, "attached_file.pdf", None
                    if isinstance(att, dict):
                        att_name = att.get("filename") or att.get("name") or "attached_file.pdf"
                        att_id   = att.get("id")
                        b64 = att.get("content") or att.get("data") or ""
                        if b64:
                            try:
                                import base64; file_bytes = base64.b64decode(b64)
                            except Exception: pass
                        if not file_bytes:
                            dl_url = att.get("url") or att.get("download_url") or ""
                            if dl_url:
                                try:
                                    r = urllib.request.Request(dl_url, headers={"Authorization": f"Bearer {_resend_key}", "User-Agent": "Mozilla/5.0"}, method="GET")
                                    with urllib.request.urlopen(r) as resp: file_bytes = resp.read()
                                except Exception: pass
                    if not file_bytes and email_id and _resend_key:
                        file_bytes = download_resend_attachment(email_id, att_id, att_name, _resend_key)
                    if file_bytes:
                        fk = f"{target_folder}{att_name}"
                        s3client.put_object(Bucket=bucket, Key=fk, Body=file_bytes, ACL='private')
                        saved_attachments.append(fk)

                if saved_attachments and comm_id:
                    try:
                        upd_conn = get_db_connection()
                        with upd_conn.cursor() as cur:
                            cur.execute("UPDATE customer_communications SET attachments_json = %s WHERE id = %s;",
                                        (json.dumps(saved_attachments, default=str), comm_id))
                            upd_conn.commit()
                        upd_conn.close()
                    except Exception as e_upd:
                        print(f"[ATTACHMENT UPDATE ERROR] {e_upd}")
    except Exception as e_s3:
        print(f"[S3 PROCESSING ERROR - non-fatal] {e_s3}")

    # 3. Non-blocking Team Email Alert
    try:
        _alert_key = os.environ.get("RESEND_API_KEY")
        team_email = get_resend_to_email()
        if _alert_key and team_email:
            att_note = f"\n\n📎 {len(saved_attachments)} Attachment(s) Saved!" if saved_attachments else ""
            alert_payload = {
                "from": format_resend_from_header(f"{parent_name or 'VRT Services'} CRM Alerts"),
                "to": [team_email],
                "subject": f"📩 New Reply Received: {legal_name} - {subject}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #7f00ff; border-radius: 12px; background: #0f172a; color: #f8fafc;">
                    <h2 style="color: #38bdf8; margin-top: 0;">📩 New Customer Email Reply Received</h2>
                    <p><strong>Customer:</strong> {legal_name} (ID: {customer_id})</p>
                    <p><strong>From:</strong> {sender_email}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <div style="background: #1e293b; padding: 14px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; margin: 16px 0; border-left: 4px solid #38bdf8; color: #e2e8f0;">
                        {body_text[:800] if body_text else '(no body)'}
                    </div>
                    {f'<p style="color: #34d399;"><strong>{att_note}</strong></p>' if saved_attachments else ''}
                </div>
                """
            }
            alert_req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(alert_payload, default=str).encode("utf-8"),
                headers={"Authorization": f"Bearer {_alert_key.strip()}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                method="POST"
            )
            with urllib.request.urlopen(alert_req) as _:
                print(f"[TEAM ALERT SENT] to {team_email}")
    except Exception as e_alert:
        print(f"[TEAM ALERT ERROR] {e_alert}")

@app.post("/api/webhooks/resend-inbound")
@app.post("/api/webhook/resend-inbound")
@app.post("/api/webhooks/resend")
@app.post("/api/webhook/resend")
@app.post("/api/inbound")
@app.post("/api/resend/inbound")
async def resend_inbound_webhook(request: Request, background_tasks: BackgroundTasks):
    """Public webhook receiver for customer reply emails forwarded from Resend."""
    global LAST_INBOUND_DEBUG
    raw_body = {}
    data = {}
    debug_log_id = None
    customer_id = None
    sender_email = ""
    recipient_email = ""
    subject = ""
    body_text = ""
    attachments = []
    cust = None
    comm_id = None

    conn = None
    try:
        try:
            raw_body = await request.json()
        except Exception:
            raw_body = {}

        try:
            print(f"[RESEND INBOUND RAW PAYLOAD]: {json.dumps(raw_body, default=str)}")
        except Exception:
            pass

        if isinstance(raw_body, dict) and "data" in raw_body and isinstance(raw_body["data"], dict):
            data = raw_body["data"]
        else:
            data = raw_body if isinstance(raw_body, dict) else {}

        def extract_email_str(val):
            if isinstance(val, list):
                val = val[0] if len(val) > 0 else ""
            if isinstance(val, dict):
                val = val.get("email") or val.get("address") or str(val)
            s = str(val or "").strip()
            s = re.sub(r"[\[\]'\"`]", "", s).strip()
            return s

        raw_sender = extract_email_str(data.get("from") or data.get("sender") or raw_body.get("from"))
        sender_email = parse_clean_email(raw_sender) or raw_sender

        raw_recipient = extract_email_str(data.get("to") or data.get("recipient") or raw_body.get("to"))
        recipient_email = parse_clean_email(raw_recipient) or raw_recipient

        def clean_html_to_text(html_str: str) -> str:
            if not html_str or not isinstance(html_str, str):
                return ""
            import html as _html_lib
            text = re.sub(r'<(?:br|p|div|tr|h\d|li)[^>]*>', '\n', html_str, flags=re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            text = _html_lib.unescape(text)
            text = re.sub(r'\n\s*\n', '\n\n', text).strip()
            return text

        def extract_email_body(raw_b: dict, d: dict) -> str:
            for obj in [d, raw_b]:
                if isinstance(obj, dict):
                    for key in ["text", "plain", "text_body", "body_text", "snippet", "preview"]:
                        val = obj.get(key)
                        if val and isinstance(val, str) and val.strip(): return val.strip()
            for obj in [d, raw_b]:
                if isinstance(obj, dict):
                    for key in ["html", "html_body", "body", "content", "message"]:
                        val = obj.get(key)
                        if val and isinstance(val, str) and val.strip():
                            cleaned = clean_html_to_text(val)
                            if cleaned:
                                return cleaned
            return ""

        subject = str(
            data.get("subject") or 
            (raw_body.get("subject") if isinstance(raw_body, dict) else "") or 
            ""
        ).strip()

        body_text = extract_email_body(raw_body if isinstance(raw_body, dict) else {}, data if isinstance(data, dict) else {})
        attachments = (
            data.get("attachments") or 
            data.get("files") or 
            data.get("documents") or 
            (raw_body.get("attachments") if isinstance(raw_body, dict) else None) or 
            []
        )

        email_id = (
            data.get("email_id") or data.get("id") or 
            (raw_body.get("email_id") if isinstance(raw_body, dict) else None) or
            (raw_body.get("data", {}).get("email_id") if isinstance(raw_body, dict) and isinstance(raw_body.get("data"), dict) else None)
        )

        # OPEN SINGLE DEDICATED DB CONNECTION FOR THE ENTIRE REQUEST
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO webhook_debug_log (payload_json, sender_email, recipient_email, subject, body_text, customer_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'RECEIVED')
                    RETURNING id;
                """, (
                    json.dumps(raw_body, default=str)[:65000],
                    sender_email[:255] if sender_email else "",
                    recipient_email[:255] if recipient_email else "",
                    subject[:500] if subject else "",
                    body_text[:1000] if body_text else "",
                    None
                ))
                row_dbg = cur.fetchone()
                if row_dbg:
                    debug_log_id = row_dbg["id"] if isinstance(row_dbg, dict) else row_dbg[0]
                conn.commit()
        except Exception as e_dbg_init:
            print(f"[WEBHOOK DB LOG INIT ERROR]: {e_dbg_init}")
            # CRITICAL: rollback so the connection is clean for the main insert below
            try:
                if conn: conn.rollback()
            except Exception:
                pass

        # 1. Filter status events
        event_type = str(raw_body.get("type") or data.get("type") or "").strip().lower()
        ignored_status_events = {"email.sent", "email.bounced", "email.complained", "email.opened", "email.clicked", "sent", "bounced", "complained", "opened", "clicked"}
        if event_type in ignored_status_events:
            print(f"[RESEND WEBHOOK IGNORED] Ignoring status event type '{event_type}'")
            return {"status": "ignored", "reason": f"Event type '{event_type}' is status event"}

        # 2. Filter self-generated CRM alerts
        if subject.startswith("📩 New Reply Received") or "CRM Alerts" in str(subject):
            print(f"[RESEND WEBHOOK IGNORED] Ignoring self-generated CRM alert email")
            return {"status": "ignored", "reason": "Self-generated CRM alert email"}

        def extract_all_customer_candidates(subj_str: str, body_str: str):
            def scan_text(txt: str):
                res = []
                if not txt or not isinstance(txt, str):
                    return res
                for m in re.finditer(r'\[\s*(?:Ref:\s*)?(?:CUST[-_\s]*)?(\d{1,6})\s*\]', txt, re.IGNORECASE):
                    res.append(f"CUST-{m.group(1)}")
                    res.append(m.group(1))
                for m in re.finditer(r'\bCUST[-_\s]*(\d{1,6})\b', txt, re.IGNORECASE):
                    res.append(f"CUST-{m.group(1)}")
                    res.append(m.group(1))
                for m in re.finditer(r'\bRef:\s*(?:CUST-)?(\d{1,6})\b', txt, re.IGNORECASE):
                    res.append(f"CUST-{m.group(1)}")
                    res.append(m.group(1))
                for m in re.finditer(r'\b(?:Customer|Cust|Client|Account|ID|#)\s*:?\s*#?\s*(?:CUST-)?(\d{1,6})\b', txt, re.IGNORECASE):
                    res.append(f"CUST-{m.group(1)}")
                    res.append(m.group(1))
                for m in re.finditer(r'\b(\d{4,5})\b', txt):
                    num = m.group(1)
                    if num != "0000":
                        res.append(f"CUST-{num}")
                        res.append(num)
                return res

            subj_cands = scan_text(subj_str)
            body_cands = scan_text(body_str)
            seen = set()
            unique = []
            for c in subj_cands + body_cands:
                c_clean = str(c).strip().upper()
                if c_clean and c_clean not in seen:
                    seen.add(c_clean)
                    unique.append(c_clean)
            return unique

        cust_candidates = extract_all_customer_candidates(subject, body_text)
        print(f"[RESEND INBOUND ROUTING] Extracted candidates for '{subject}': {cust_candidates}")

        # Always use a FRESH dedicated connection for the main processing block
        # The debug-log conn may be in a broken state; don't reuse it here
        main_conn = None
        try:
            main_conn = get_db_connection()

            with main_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # ── Step 1: Deduplication Check ──
                if email_id and len(str(email_id).strip()) > 3:
                    clean_eid = str(email_id).strip()
                    dup_json = json.dumps([{"email_id": clean_eid}])
                    cur.execute("""
                        SELECT id FROM customer_communications
                        WHERE direction = 'INBOUND'
                          AND attachments_json @> %s::jsonb;
                    """, (dup_json,))
                    if cur.fetchone():
                        print(f"[RESEND DUP IGNORED] Duplicate email_id '{email_id}' already saved!")
                        if debug_log_id:
                            cur.execute("UPDATE webhook_debug_log SET status = 'IGNORED_DUP' WHERE id = %s;", (debug_log_id,))
                            main_conn.commit()
                        return {"status": "ignored", "reason": f"Duplicate email_id '{email_id}'"}

                # ── Step 2: Customer Matching ──
                for cand in cust_candidates:
                    raw_digits = re.sub(r'[^\d]', '', cand)
                    if not raw_digits or raw_digits == "0000":
                        continue
                    clean_cust = f"CUST-{raw_digits}"
                    clean_cust_no_dash = f"CUST{raw_digits}"
                    cur.execute("""
                        SELECT id, legal_name, parent_name, customer_type FROM customer 
                        WHERE custumer_number ILIKE %s 
                           OR custumer_number ILIKE %s 
                           OR custumer_number ILIKE %s
                           OR regexp_replace(custumer_number, '[^0-9]', '', 'g') = %s
                           OR id::text = %s;
                    """, (cand, clean_cust, clean_cust_no_dash, raw_digits, raw_digits))
                    found = cur.fetchone()
                    if found:
                        cust = found
                        print(f"[RESEND ROUTING MATCH] Candidate '{cand}' -> Customer #{cust['id']} ({cust['legal_name']})")
                        break

                # Fallback: Match by Sender Email if no Customer ID candidate matched
                if not cust and sender_email and len(sender_email.strip()) > 3:
                    clean_se = sender_email.strip().lower()
                    cur.execute("""
                        SELECT id, legal_name, parent_name, customer_type FROM customer
                        WHERE LOWER(email) = %s OR LOWER(email) LIKE %s;
                    """, (clean_se, f"%{clean_se}%"))
                    found_by_email = cur.fetchone()
                    if found_by_email:
                        cust = found_by_email
                        print(f"[RESEND ROUTING MATCH BY SENDER EMAIL] '{sender_email}' -> Customer #{cust['id']} ({cust['legal_name']})")

                if not cust:
                    print(f"[RESEND ROUTING FALLBACK] No Customer ID match for '{subject}'. Routing to CUST-0000.")
                    cur.execute("SELECT id, legal_name, parent_name, customer_type FROM customer WHERE custumer_number = 'CUST-0000';")
                    cust = cur.fetchone()
                    if not cust:
                        cur.execute("""
                            INSERT INTO customer (
                                custumer_number, customer_type, legal_name, display_name,
                                status, parent_name, created_at, updated_at
                            ) VALUES (
                                'CUST-0000', 'System', 'Unassigned Inbound Emails', 'Unassigned / General Inbox',
                                'Active', 'VRT Services', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            ) RETURNING id, legal_name, parent_name, customer_type;
                        """)
                        cust = cur.fetchone()

                customer_id = cust["id"] if cust else None
                legal_name = cust["legal_name"] if cust else "Unassigned Customer"
                parent_name = (cust.get("parent_name") if cust else None) or "VRT Services"

                # ── Step 3: Insert into customer_communications ──
                # Use email_id as message_id for clean deduplication (not via attachments_json)
                init_atts = [{"email_id": str(email_id)}] if email_id else []
                final_body = body_text.strip() if body_text and isinstance(body_text, str) and body_text.strip() else f"Subject: {subject}"

                # Truncate to match exact DB column sizes: sender_email/recipient_email VARCHAR(200), subject VARCHAR(300)
                safe_sender = (sender_email or "")[:199]
                safe_recipient = (recipient_email or "")[:199]
                safe_subject = (subject or "")[:299]

                cur.execute("""
                    INSERT INTO customer_communications (
                        customer_id, direction, sender_email, recipient_email,
                        subject, body_text, attachments_json, status, is_read, created_at
                    ) VALUES (
                        %s, 'INBOUND', %s, %s, %s, %s, %s::jsonb, 'UNREAD', FALSE, CURRENT_TIMESTAMP
                    ) RETURNING id;
                """, (customer_id, safe_sender, safe_recipient, safe_subject, final_body, json.dumps(init_atts, default=str)))

                comm_row = cur.fetchone()
                comm_id = comm_row["id"] if isinstance(comm_row, dict) else (comm_row[0] if comm_row else None)

                # ── Step 4: Update webhook_debug_log status to SUCCESS ──
                if debug_log_id:
                    cur.execute("""
                        UPDATE webhook_debug_log SET status = 'SUCCESS', customer_id = %s WHERE id = %s;
                    """, (customer_id, debug_log_id))
                main_conn.commit()
                print(f"[RESEND INBOUND WEBHOOK] ✅ SUCCESS saved comm_id={comm_id} to customer '{legal_name}' (ID: {customer_id})")

        except Exception as e_main:
            import traceback
            print(f"[RESEND MAIN INSERT ERROR] {e_main}")
            traceback.print_exc()
            try:
                if main_conn: main_conn.rollback()
                if debug_log_id and main_conn:
                    with main_conn.cursor() as cur_err:
                        cur_err.execute("UPDATE webhook_debug_log SET status = %s WHERE id = %s;",
                                        (f"ERROR: {str(e_main)[:190]}", debug_log_id))
                        main_conn.commit()
            except Exception:
                pass
            raise  # Let the outer except handle it and return error response
        finally:
            if main_conn:
                try: main_conn.close()
                except Exception: pass

        LAST_INBOUND_DEBUG = {
            "received_at": str(datetime.datetime.now()),
            "raw_body": raw_body,
            "sender_email": sender_email,
            "recipient_email": recipient_email,
            "subject": subject,
            "extracted_body_text": body_text,
            "customer_id": customer_id,
            "attachments_count": len(attachments) if 'attachments' in locals() else 0
        }

        # Dispatch async background tasks for Resend body fetch, S3 attachment uploads, and Team Email Alerts
        background_tasks.add_task(
            process_inbound_post_processing,
            email_id=str(email_id) if email_id else "",
            comm_id=comm_id,
            customer_id=customer_id,
            legal_name=legal_name,
            parent_name=parent_name,
            subject=subject,
            sender_email=sender_email,
            body_text=body_text,
            raw_body=raw_body,
            data=data,
            attachments=attachments
        )

        return {"status": "success", "customer_id": customer_id, "comm_id": comm_id}

    except Exception as e:
        import traceback
        err_msg = f"OUTER_ERROR: {e}"
        print(f"Error handling Resend Inbound Webhook: {err_msg}")
        traceback.print_exc()
        if conn and debug_log_id:
            try:
                conn.rollback()
                with conn.cursor() as cur:
                    cur.execute("UPDATE webhook_debug_log SET status = %s, customer_id = %s WHERE id = %s;", (err_msg[:200], customer_id, debug_log_id))
                    conn.commit()
            except Exception as e_rb:
                print(f"[WEBHOOK ROLLBACK DB UPDATE ERROR]: {e_rb}")
        return {"status": "error", "message": str(e)}

    finally:
        if conn:
            try: conn.close()
            except Exception: pass

# ── Health / debug ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    import json as _json
    
    # 1. Check Google Vision credentials
    google_status = "error"
    google_detail = "MISSING"
    google_error = None
    
    # Check GOOGLE_CREDENTIALS_JSON env var
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if creds_raw:
        creds_stripped = creds_raw.strip().strip('"\'')
        try:
            info = _json.loads(creds_stripped)
            google_status = "ok"
            google_detail = f"GOOGLE_CREDENTIALS_JSON: OK — project_id={info.get('project_id')}, client_email={info.get('client_email')}"
        except Exception as e:
            google_detail = "GOOGLE_CREDENTIALS_JSON: INVALID JSON"
            google_error = str(e)
            
    # Check GOOGLE_APPLICATION_CREDENTIALS file path
    if google_status != "ok":
        env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path:
            env_path_stripped = env_path.strip().strip('"\'')
            if os.path.exists(env_path_stripped):
                google_status = "ok"
                google_detail = f"GOOGLE_APPLICATION_CREDENTIALS file exists: {env_path_stripped}"
            else:
                google_detail = f"GOOGLE_APPLICATION_CREDENTIALS path specified but file not found: {env_path_stripped}"
                
    # Check Fallback paths
    if google_status != "ok":
        fallback_paths = [
            r"C:\keys\vision-keyvtr.json",
            r"/keys/vision-keyvtr.json",
            r"C:\keys\vision-key.json",
            r"/keys/vision-key.json",
        ]
        for path in fallback_paths:
            if os.path.exists(path):
                google_status = "ok"
                google_detail = f"Fallback file exists: {path}"
                break

    # 2. Check Support Email (Resend) credentials
    resend_key = (
        os.environ.get("RESEND_API_KEY") or
        os.environ.get("RESEND_KEY") or
        os.environ.get("RESEND_API_TOKEN") or
        os.environ.get("RESEND_TOKEN")
    )
    
    resend_status = "error"
    resend_detail = "MISSING"
    
    if resend_key:
        resend_key = resend_key.strip().strip('\'"')
        if resend_key.startswith("re_"):
            resend_status = "ok"
            masked_key = f"{resend_key[:6]}...{resend_key[-4:]}" if len(resend_key) > 10 else "re_..."
            resend_detail = f"Configured (API Key: {masked_key})"
        else:
            resend_detail = "Invalid API Key format (Must start with 're_')"
            
    from_email = get_resend_from_email()
    to_email = get_resend_to_email()

    # Overall health check status (depends primarily on extraction pipeline's Google Vision capability)
    overall_status = "ok" if google_status == "ok" else "error"
    
    return {
        "status": overall_status,
        "google_vision": {
            "status": google_status,
            "detail": google_detail,
            "error": google_error
        },
        "support_email": {
            "status": resend_status,
            "detail": resend_detail,
            "from_email": from_email,
            "to_email": get_resend_to_email(),
            "reply_to_email": get_resend_reply_to_email()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, reload_includes=["*.py", "*.html", "*.js"])

