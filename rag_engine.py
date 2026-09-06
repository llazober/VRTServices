import os
import re
import json
import math
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
import datetime

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")

def get_tenant_slug(parent_name: str) -> str:
    """Normalize parent client name to directory slug."""
    if not parent_name:
        return "vrt_services"
    p_lower = str(parent_name).lower()
    if "datalazo" in p_lower:
        return "datalazo_llc"
    return "vrt_services"

def load_knowledge_chunks(tenant_slug: str) -> List[Dict[str, Any]]:
    """Load and chunk markdown files strictly for a specific tenant."""
    chunks = []
    dirs_to_load = [
        os.path.join(KB_DIR, tenant_slug)
    ]
    
    for d in dirs_to_load:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith(".md") or file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                            
                        # Split by headers (## or #) or paragraphs
                        raw_sections = re.split(r'\n(?=#{1,3}\s)', text)
                        for sec in raw_sections:
                            clean_sec = sec.strip()
                            if len(clean_sec) > 20:
                                chunks.append({
                                    "source": file,
                                    "category": "tax" if "shared_irs_tax" in d else "company",
                                    "content": clean_sec
                                })
                    except Exception as e:
                        print(f"[RAG LOAD ERROR] Failed loading {file_path}: {e}")
    return chunks

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r'\b\w{3,}\b', text)]

def retrieve_relevant_passages(query: str, tenant_slug: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Simple TF-IDF / Cosine-similarity vector search over knowledge chunks."""
    chunks = load_knowledge_chunks(tenant_slug)
    if not chunks:
        return []
        
    query_tokens = tokenize(query)
    if not query_tokens:
        return chunks[:top_k]

    scores = []
    query_lower = query.lower()
    for chunk in chunks:
        content_lower = chunk["content"].lower()
        chunk_tokens = tokenize(chunk["content"])
        if not chunk_tokens:
            scores.append((0, chunk))
            continue
            
        # Match score calculation
        matches = sum(1 for t in query_tokens if t in chunk_tokens)
        overlap_score = matches / (math.sqrt(len(query_tokens)) * math.sqrt(len(chunk_tokens)) + 1e-5)
        
        # Boost exact keyword matches
        for t in query_tokens:
            if t in content_lower:
                overlap_score += 0.25
                
        # Boost exact title / filename match (e.g. "preset schedule" -> "Generate_Preset_Schedule.md")
        source_name = chunk.get("source", "").lower().replace(".md", "").replace("_", " ")
        if query_lower in source_name or any(t in source_name for t in query_tokens if len(t) > 3):
            overlap_score += 1.0
                
        scores.append((overlap_score, chunk))

    scores.sort(key=lambda x: x[0], reverse=True)
    if not scores or scores[0][0] <= 0.1:
        return []

    top_score = scores[0][0]
    filtered_passages = []
    for score, chunk in scores[:top_k]:
        # Only keep secondary passages if they are close in relevance score (at least 65% of top score)
        if score > 0.2 and (score >= top_score * 0.65):
            filtered_passages.append(chunk)

    return filtered_passages

def get_customer_task_status(cur, customer_ref: str, parent_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve customer profile and task checklist progress from database with separate Bookkeeping & Tax In Process periods."""
    if not customer_ref:
        return None
        
    clean_ref = str(customer_ref).strip()
    cust_num_with_prefix = f"CUST-{clean_ref}" if not clean_ref.upper().startswith("CUST-") else clean_ref
    cust_num_raw = clean_ref.replace("CUST-", "").replace("cust-", "")

    tenant_slug = get_tenant_slug(parent_name)
    filter_parent = "VRT Services" if tenant_slug == "vrt_services" else "Datalazo LLC"

    cur.execute("""
        SELECT id, custumer_number, legal_name, display_name, email, parent_name, customer_type, created_at
        FROM customer 
        WHERE (custumer_number ILIKE %s OR custumer_number ILIKE %s OR id::text = %s)
          AND (parent_name ILIKE %s OR parent_name ILIKE %s OR parent_name IS NULL OR parent_name = '');
    """, (clean_ref, cust_num_with_prefix, cust_num_raw, f"%{filter_parent}%", filter_parent))
    cust = cur.fetchone()
    if not cust:
        return None

    customer_id = cust["id"]
    is_individual = (cust.get("customer_type") or "").lower() == "individual"

    from app import get_in_process_period
    bk_slug, bk_label = get_in_process_period(cur, customer_id, "bookkeeping")
    tax_slug, tax_label = get_in_process_period(cur, customer_id, "tax")

    # Fetch rows independently
    cur.execute("""
        SELECT * FROM customer_task_checklist
        WHERE customer_id = %s AND period = %s;
    """, (customer_id, bk_slug))
    bk_row = cur.fetchone() or {}

    cur.execute("""
        SELECT * FROM customer_task_checklist
        WHERE customer_id = %s AND period = %s;
    """, (customer_id, tax_slug))
    tax_row = cur.fetchone() or {}

    bk_task_defs = [
        ("bank_statement_received", "Bank Statements Received", "Bookkeeping"),
        ("check_images_received", "Check Images Received", "Bookkeeping"),
        ("extraction_ai_categorization_done", "OCR Transaction Extraction", "Bookkeeping"),
        ("accountant_reviewed", "Accountant Review", "Bookkeeping")
    ]
    tax_task_defs = [
        ("tax_docs_requested", "Tax Documents Requested", "Tax Return"),
        ("tax_docs_received", "Tax Documents Received", "Tax Return"),
        ("tax_organizer", "Tax Organizer Completed", "Tax Return"),
        ("tax_preparation", "Tax Return Preparation", "Tax Return"),
        ("tax_review", "Tax Return Review", "Tax Return"),
        ("tax_client_signature", "Form 8879 Client Signature", "Tax Return"),
        ("tax_efile", "IRS E-Filing Transmitted", "Tax Return"),
        ("tax_accepted", "IRS Return Accepted", "Tax Return")
    ]

    bk_checklist = []
    bk_completed = 0
    if not is_individual:
        for key, label, cat in bk_task_defs:
            is_done = bool(bk_row.get(key, False))
            if is_done: bk_completed += 1
            bk_checklist.append({
                "item_key": key,
                "item_label": label,
                "category": cat,
                "is_completed": is_done
            })
    bk_percent = int((bk_completed / 4.0) * 100) if not is_individual else 100

    tax_checklist = []
    tax_completed = 0
    for key, label, cat in tax_task_defs:
        is_done = bool(tax_row.get(key, False))
        if is_done: tax_completed += 1
        tax_checklist.append({
            "item_key": key,
            "item_label": label,
            "category": cat,
            "is_completed": is_done
        })
    tax_percent = int((tax_completed / 8.0) * 100)

    total_tasks = tax_completed if is_individual else (bk_completed + tax_completed)
    max_tasks = 8 if is_individual else 12
    overall_percent = int((total_tasks / max_tasks) * 100)

    return {
        "customer_id": customer_id,
        "customer_number": cust.get("custumer_number") or f"CUST-{customer_id}",
        "legal_name": cust.get("legal_name"),
        "customer_type": cust.get("customer_type"),
        "is_individual": is_individual,
        "email": cust.get("email"),
        "parent_name": cust.get("parent_name"),
        "bk_period": bk_slug,
        "bk_period_label": bk_label,
        "bk_completed": bk_completed,
        "bk_percent": bk_percent,
        "bk_checklist": bk_checklist,
        "tax_period": tax_slug,
        "tax_period_label": tax_label,
        "tax_completed": tax_completed,
        "tax_percent": tax_percent,
        "tax_checklist": tax_checklist,
        "total_tasks": max_tasks,
        "completed_tasks": total_tasks,
        "progress_percent": overall_percent
    }

def synthesize_ai_response(user_query: str, parent_name: str, status_info: Optional[Dict] = None, passages: List[Dict] = None, customer_ref_not_found: bool = False, searched_ref: str = None) -> str:
    """Synthesize final Chatbot response using Gemini, OpenAI, or Fallback Synthesizer."""
    gemini_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    provider = (os.environ.get("AI_PROVIDER") or "").strip().upper()

    company_name = "VRT Services" if get_tenant_slug(parent_name) == "vrt_services" else "Datalazo LLC"

    # Context Construction
    context_str = f"Target Company: {company_name}\n"
    if status_info:
        context_str += f"\n--- LIVE CUSTOMER TASK STATUS ---\n"
        context_str += f"Customer: {status_info['legal_name']} ({status_info['customer_number']})\n"
        
        if not status_info.get("is_individual"):
            context_str += f"Bookkeeping Cycle: {status_info['bk_period_label']} ({status_info['bk_percent']}% Completed, {status_info['bk_completed']}/4 steps)\n"
            for item in status_info["bk_checklist"]:
                status_symbol = "✅ DONE" if item["is_completed"] else "⏳ PENDING"
                context_str += f"- [{status_symbol}] {item['item_label']} (Bookkeeping)\n"
        
        context_str += f"Tax Preparation Year: {status_info['tax_period_label']} ({status_info['tax_percent']}% Completed, {status_info['tax_completed']}/8 steps)\n"
        for item in status_info["tax_checklist"]:
            status_symbol = "✅ DONE" if item["is_completed"] else "⏳ PENDING"
            context_str += f"- [{status_symbol}] {item['item_label']} (Tax Return)\n"
    elif customer_ref_not_found and searched_ref:
        context_str += f"\n--- CUSTOMER SEARCH NOTICE ---\n"
        context_str += f"The customer reference code '{searched_ref}' was NOT found in the database for {company_name}.\n"
        context_str += f"Inform the user clearly that customer reference code '{searched_ref}' does not exist in our database. Ask them to verify their reference code (e.g. CUST-1001) or contact support.\n"
            
    if passages:
        context_str += f"\n--- KNOWLEDGE BASE PASSAGES ---\n"
        for p in passages:
            context_str += f"Source ({p['source']}):\n{p['content']}\n\n"

    system_prompt = (
        f"You are the official AI Knowledge Assistant for {company_name}. "
        "Your goal is to provide concise, friendly, accurate, and professional help to clients and visitors. "
        "Always use clean Markdown formatting (bolding, bullet points, checklists). "
        "If answering a customer task status query, clearly specify the Bookkeeping Period (e.g. July 2026) and Tax Preparation Year (e.g. Tax Year 2025), along with their progress and pending actions. "
        "If a customer reference code was searched but NOT found in the database, explicitly state that the customer reference code does not exist in our records and ask them to verify their reference code (e.g., CUST-1001) or contact support. "
        "If giving general tax information, add a brief note that information is for guidance and formal advice is finalized upon review."
    )

    # 1. Try Google Gemini API first if configured
    if gemini_key and (provider == "GEMINI" or not openai_key):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\nContext:\n{context_str}\n\nUser Question: {user_query}"}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 600
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e_gem:
            print(f"[RAG GEMINI API NOTICE]: {e_gem}")

    # 2. Try OpenAI API if configured
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {user_query}"}
                ],
                "temperature": 0.3,
                "max_tokens": 600
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
        except Exception as e_oai:
            print(f"[RAG OPENAI API NOTICE]: {e_oai}")

    # 3. Fallback Formatter (Zero API key / offline mode)
    res_lines = []
    if status_info:
        res_lines.append(f"### 📋 Task Progress Report — {status_info['legal_name']}")
        res_lines.append(f"**Reference Number:** `{status_info['customer_number']}`\n")
        
        if not status_info.get("is_individual"):
            res_lines.append(f"📊 **Bookkeeping Cycle ({status_info['bk_period_label']}):** `{status_info['bk_percent']}% Completed` ({status_info['bk_completed']}/4 steps)")
            for item in status_info["bk_checklist"]:
                icon = "✅" if item["is_completed"] else "⏳"
                res_lines.append(f"- {icon} **{item['item_label']}** (`Bookkeeping`)")
            res_lines.append("")

        res_lines.append(f"📑 **Tax Preparation ({status_info['tax_period_label']}):** `{status_info['tax_percent']}% Completed` ({status_info['tax_completed']}/8 steps)")
        for item in status_info["tax_checklist"]:
            icon = "✅" if item["is_completed"] else "⏳"
            res_lines.append(f"- {icon} **{item['item_label']}** (`Tax Return`)")
            
        res_lines.append("\n*To send additional files or inquire further, reply directly to your portal emails or upload via customer storage.*")
    elif customer_ref_not_found and searched_ref:
        res_lines.append(f"⚠️ **Customer Reference Code Not Found**\n")
        res_lines.append(f"We could not find any active customer record matching reference code **`{searched_ref}`** for **{company_name}**.\n")
        res_lines.append("Please verify your reference number (e.g. `CUST-1001`) and try again, or contact our support team if you need further assistance.")
    elif passages:
        res_lines.append(f"### ℹ️ {company_name} Knowledge Answer\n")
        passage_texts = [p["content"].strip() for p in passages]
        res_lines.append("\n\n---\n\n".join(passage_texts))
    else:
        res_lines.append(f"Welcome to **{company_name}** Assistant!\n")
        res_lines.append("How can I assist you today?")
        res_lines.append("- Ask a tax or filing question (e.g. *IRS Form 8879 rules* or *business mileage deduction*).")
        res_lines.append("- Consult your customer task progress by typing your reference code (e.g. `CUST-1001`).")

    return "\n".join(res_lines)
