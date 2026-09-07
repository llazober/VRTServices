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
    """Load all document_chunk and document rows unconditionally from PostgreSQL so no data is ever filtered out."""
    chunks = []
    try:
        from app import get_db_connection
        from psycopg2.extras import RealDictCursor
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Fetch ALL chunks unconditionally from document_chunk table
            cur.execute("""
                SELECT c.content, 
                       COALESCE(d.title, c.tenant_slug, 'Documentation') AS title, 
                       COALESCE(d.rel_path, c.tenant_slug, 'knowledge') AS source, 
                       COALESCE(d.category, 'Documentation') AS category
                FROM document_chunk c
                LEFT JOIN document d ON c.document_id = d.id;
            """)
            rows = cur.fetchall() or []
            for r in rows:
                if r.get("content"):
                    chunks.append({
                        "source": r.get("source") or "document",
                        "title": r.get("title") or "Knowledge Article",
                        "category": r.get("category") or "Documentation",
                        "content": r["content"]
                    })

            # 2. Also check document table for any unchunked content
            cur.execute("""
                SELECT id, title, rel_path, category, content, tenant_slug
                FROM document;
            """)
            doc_rows = cur.fetchall() or []
            for d_row in doc_rows:
                source = d_row.get("rel_path") or ""
                if not any(c.get("source") == source for c in chunks):
                    doc_content = d_row.get("content", "")
                    if doc_content.strip():
                        raw_sections = re.split(r'\n(?=#{1,3}\s)', doc_content)
                        for sec in raw_sections:
                            clean_sec = sec.strip()
                            if len(clean_sec) > 10:
                                chunks.append({
                                    "source": source,
                                    "title": d_row.get("title") or "Document",
                                    "category": d_row.get("category") or "Documentation",
                                    "content": clean_sec
                                })

        conn.close()
    except Exception as e:
        print(f"[RAG DB CHUNK LOAD ERROR] {e}")

    return chunks

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r'\b\w{2,}\b', text)]

def retrieve_relevant_passages(query: str, tenant_slug: str, top_k: int = 8) -> List[Dict[str, Any]]:
    """Robust TF-IDF, intent-boosted, and keyword matching over knowledge chunks with guaranteed context fallback."""
    chunks = load_knowledge_chunks(tenant_slug)
    if not chunks:
        return []
        
    query_tokens = tokenize(query)
    if not query_tokens:
        return chunks[:top_k]

    scores = []
    query_lower = (query or "").lower().strip()
    
    for chunk in chunks:
        content_lower = (chunk.get("content") or "").lower()
        title_lower = (chunk.get("title") or "").lower()
        source_lower = (chunk.get("source") or "").lower()
        
        score = 0.0
        
        # 1. Exact full query match boost
        if query_lower and query_lower in content_lower:
            score += 20.0
        if query_lower and query_lower in title_lower:
            score += 25.0
            
        # 2. Individual token matches
        chunk_tokens = set(tokenize(content_lower))
        for t in query_tokens:
            if len(t) <= 1:
                continue
            if t in title_lower:
                score += 5.0
            if t in content_lower:
                score += 3.0
            if t in chunk_tokens:
                score += 2.0
                
        # 3. Special intent boost for contact / support / hours queries
        contact_terms = ["contact", "email", "phone", "hours", "support", "address", "location", "reach"]
        if any(term in query_lower for term in contact_terms):
            if any(term in content_lower for term in ["contact", "email", "hours", "phone", "support", "notification@", "monday", "est"]):
                score += 30.0

        scores.append((score, chunk))

    # Sort ALL chunks by score descending
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Filter chunks with score > 0 across entire database
    matching_passages = [chunk for score, chunk in scores if score > 0.0]
    
    if matching_passages:
        return matching_passages[:top_k]

    # Fallback: Return top_k chunks unconditionally if no positive scores
    return [chunk for score, chunk in scores[:top_k]]

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

def is_spanish_query(text: str) -> bool:
    """Detect if query is in Spanish or explicitly requests Spanish language."""
    if not text:
        return False
    t_lower = text.lower()
    spanish_keywords = [
        "hola", "buenos dias", "buenas tardes", "buenas noches", "español", "espanol",
        "impuesto", "impuestos", "declaracion", "contabilidad", "cliente", "gracias",
        "ayuda", "estado", "tramite", "como", "que", "donde", "cuando", "por que",
        "favor", "respuesta", "informacion", "base de datos", "revisar", "spanish"
    ]
    if any(char in text for char in ['¿', '¡', 'ñ', 'á', 'é', 'í', 'ó', 'ú']):
        return True
    words = re.findall(r'\b\w+\b', t_lower)
    return any(w in spanish_keywords for w in words)

def synthesize_ai_response(user_query: str, parent_name: str, status_info: Optional[Dict] = None, passages: List[Dict] = None, customer_ref_not_found: bool = False, searched_ref: str = None) -> str:
    """Synthesize final Chatbot response using Gemini, OpenAI, or Fallback Synthesizer."""
    gemini_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    openai_key = (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY") or "").strip()
    provider = (os.environ.get("AI_PROVIDER") or "OPENAI").strip().upper()

    company_name = "VRT Services" if get_tenant_slug(parent_name) == "vrt_services" else "Datalazo LLC"
    clean_query = (user_query or "").strip()
    is_spanish = is_spanish_query(clean_query)
    is_greeting = clean_query.lower() in [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "help", "who are you",
        "hola", "buenos dias", "buenas tardes", "buenas noches", "ayuda"
    ]

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
    elif not status_info and not customer_ref_not_found:
        context_str += f"\n--- KNOWLEDGE BASE PASSAGES ---\nNo relevant knowledge base articles or documents were found in the database for the user query: \"{clean_query}\".\n"

    lang_instruction = (
        "CRITICAL LANGUAGE INSTRUCTION: The user query is in SPANISH (or requests Spanish). "
        "You MUST provide your entire response in clear, fluent, professional Spanish. "
        "If no information is found in the knowledge base, state explicitly in Spanish: "
        f"'Lo siento, pero no tengo información sobre **{clean_query}** en nuestra Base de Conocimientos.'"
        if is_spanish else
        "LANGUAGE INSTRUCTION: Match the user's language. If the user asks in Spanish, respond in professional Spanish. "
        "If no information is found in the knowledge base, state explicitly: "
        f"'I am sorry, but I do not have information about **{clean_query}** in our Knowledge Base.'"
    )

    system_prompt = (
        f"You are the official AI Knowledge Assistant and Enterprise Task Agent for {company_name}. "
        "Your mission is to provide clear, friendly, precise, and highly professional assistance to clients, staff, and visitors. "
        "Formatting Standards: Always format your responses using clean, structured Markdown (bold section titles, bullet points, and code blocks). "
        "COMPREHENSIVE EXPLANATION REQUIREMENT: When asked about VRT Services or company overview, provide a full, detailed, and clear explanation of all services provided (enterprise accounting, tax preparation, bookkeeping advisory, client portal, tax organizer processing, bank statement reconciliation, and QuickBooks Online integration for individuals, LLCs, and corporations). "
        "STRICT GROUNDING REQUIREMENT: Ground all answers strictly on the provided Knowledge Base Passages and Live Customer Task Status context. "
        "Do NOT hallucinate, invent unverified pricing, make unsupported tax claims, or speculate beyond the database contents. "
        f"{lang_instruction} "
        "If the user sends a simple greeting (e.g. 'hello', 'hi', 'hola', 'buenos días'), greet them warmly and invite them to ask about company documentation, pricing, tax prep workflows, or check their customer task status by providing their reference code (e.g. CUST-4060). "
        "If answering a customer status query, present a clean breakdown of both Bookkeeping Period & Tax Return milestones, including percentage completion and completed vs pending items. "
        "If a requested customer reference code is not found in the database, explicitly inform the user that the code does not exist in our records and suggest verifying their code or contacting support."
    )

    # 1. Try OpenAI API first if key is present or AI_PROVIDER is OPENAI
    if openai_key and (provider == "OPENAI" or not gemini_key):
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {user_query}"}
                ],
                "temperature": 0.2,
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

    # 2. Try Google Gemini API secondary
    if gemini_key:
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
                    "temperature": 0.2,
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

    # 3. Fallback Formatter (Zero API key / offline mode)
    res_lines = []
    if status_info:
        if is_spanish:
            res_lines.append(f"### 📋 Reporte de Estado de Tareas — {status_info['legal_name']}")
            res_lines.append(f"**Número de Referencia:** `{status_info['customer_number']}`\n")
            if not status_info.get("is_individual"):
                res_lines.append(f"📊 **Ciclo de Contabilidad ({status_info['bk_period_label']}):** `{status_info['bk_percent']}% Completado` ({status_info['bk_completed']}/4 pasos)")
                for item in status_info["bk_checklist"]:
                    icon = "✅" if item["is_completed"] else "⏳"
                    res_lines.append(f"- {icon} **{item['item_label']}** (`Contabilidad`)")
                res_lines.append("")

            res_lines.append(f"📑 **Preparación de Impuestos ({status_info['tax_period_label']}):** `{status_info['tax_percent']}% Completado` ({status_info['tax_completed']}/8 pasos)")
            for item in status_info["tax_checklist"]:
                icon = "✅" if item["is_completed"] else "⏳"
                res_lines.append(f"- {icon} **{item['item_label']}** (`Declaración de Impuestos`)")
            res_lines.append("\n*Para enviar archivos adicionales o realizar consultas, responda directamente a sus correos del portal.*")
        else:
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
        if is_spanish:
            res_lines.append(f"⚠️ **Código de Referencia de Cliente No Encontrado**\n")
            res_lines.append(f"No pudimos encontrar ningún registro de cliente activo que coincida con el código **`{searched_ref}`** para **{company_name}**.\n")
            res_lines.append("Por favor verifique su número de referencia (ej. `CUST-1001`) e intente nuevamente, o contacte a soporte.")
        else:
            res_lines.append(f"⚠️ **Customer Reference Code Not Found**\n")
            res_lines.append(f"We could not find any active customer record matching reference code **`{searched_ref}`** for **{company_name}**.\n")
            res_lines.append("Please verify your reference number (e.g. `CUST-1001`) and try again, or contact our support team if you need further assistance.")
    elif passages:
        if is_spanish:
            res_lines.append(f"### ℹ️ Respuesta de Conocimiento de {company_name}\n")
        else:
            res_lines.append(f"### ℹ️ {company_name} Knowledge Answer\n")
        passage_texts = [p["content"].strip() for p in passages]
        res_lines.append("\n\n---\n\n".join(passage_texts))
    elif is_greeting:
        if is_spanish:
            res_lines.append(f"¡Hola! Bienvenido al Asistente de **{company_name}**.\n")
            res_lines.append("¿Cómo puedo ayudarte hoy?")
            res_lines.append("- Haz una pregunta sobre servicios fiscales o políticas (ej. *reglas Formulario IRS 8879* o *deducciones*).")
            res_lines.append("- Consulta el estado de tus tareas ingresando tu código de referencia (ej. `CUST-1001`).")
        else:
            res_lines.append(f"Hello! Welcome to **{company_name}** Assistant.\n")
            res_lines.append("How can I assist you today?")
            res_lines.append("- Ask a tax or filing question (e.g. *IRS Form 8879 rules* or *business mileage deduction*).")
            res_lines.append("- Consult your customer task progress by typing your reference code (e.g. `CUST-1001`).")
    else:
        if is_spanish:
            res_lines.append(f"Lo siento, pero no tengo información sobre **\"{clean_query}\"** en nuestra Base de Conocimientos.\n")
            res_lines.append("Por favor intenta preguntar sobre nuestras políticas de empresa, servicios fiscales o consulta tu progreso usando tu código de referencia (ej. `CUST-1001`).")
        else:
            res_lines.append(f"I am sorry, but I do not have information about **\"{clean_query}\"** in our Knowledge Base.\n")
            res_lines.append("Please try asking about our documented company policies, tax services, or check your customer task progress by typing your reference code (e.g. `CUST-1001`).")

    return "\n".join(res_lines)
