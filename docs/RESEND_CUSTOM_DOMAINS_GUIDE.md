# Resend Custom Domains & Multi-Portal Email Routing Setup (Method 1)

## Overview
This guide documents **Method 1** for configuring isolated custom domain sending and inbound email routing between multiple portals (e.g., `vrtservices12.com` and `datalazo.net`) using Resend, Cloudflare DNS, and Cloudflare Email Routing.

---

## 1. Cloudflare DNS Configuration

> **Important Note on Editing Records:**
> Cloudflare's *Email Routing* tab locks the SPF TXT record text editing. To edit the actual SPF text value, navigate to the main **DNS → Records** section in the left sidebar menu. When entering TXT content in Cloudflare UI, **do NOT paste surrounding quotation marks (`"`)**.

### A. VRT Services Domain (`vrtservices12.com`)
- **DKIM (TXT):**
  - Name: `resend._domainkey.vrtservices12.com`
  - Value: Resend DKIM public key
- **SPF (TXT):**
  - Name: `vrtservices12.com`
  - Value: `v=spf1 include:spf.efwd.registrar-servers.com include:_spf.mx.cloudflare.net include:resend.com ~all`
- **DMARC (TXT):**
  - Name: `_dmarc.vrtservices12.com`
  - Value: `v=DMARC1; p=none; rua=mailto:...`

### B. Datalazo CRM Domain (`datalazo.net`)
- **DKIM (TXT):**
  - Name: `resend._domainkey.datalazo.net`
  - Value: Resend DKIM public key
- **SPF (TXT):**
  - Name: `datalazo.net`
  - Value: `v=spf1 include:spf.privateemail.com include:resend.com ~all`
- **DMARC (TXT):**
  - Name: `_dmarc.datalazo.net`
  - Value: `v=DMARC1; p=none; rua=mailto:...`

---

## 2. Cloudflare Email Routing (Inbound Forwarding)

To forward incoming custom domain emails (e.g. `notification@vrtservices12.com`) into Resend:

### Step 1: Destination Address Verification
1. Navigate to **Email → Email Routing → Destination Addresses** in Cloudflare.
2. Click **Add address** and enter the Resend inbound email for the portal:
   - For VRT Services: `vrt@ostooechei.resend.app`
   - For Datalazo CRM: `crm@ostooechei.resend.app`
3. Cloudflare sends a verification link email to that address.
4. Resend receives the verification email and triggers your portal webhook `/api/webhooks/resend-inbound`.
5. Check your portal logs (`/api/debug/last-inbound`) or portal inbox for the Cloudflare link and click **Verify**.

### Step 2: Create Routing Rules
1. Navigate to **Email → Email Routing → Routing rules** in Cloudflare.
2. Click **Create routing rule**:
   - **Email pattern:** `notification` @ `vrtservices12.com`
   - **Action:** Send to an email
   - **Destination:** `vrt@ostooechei.resend.app`
3. Ensure rule status is set to **Active**.

---

## 3. Resend Dashboard Verification & Webhook Binding

1. **Verify Domains:**
   - Navigate to [Resend Dashboard → Domains](https://resend.com/domains).
   - Click **Verify** on `vrtservices12.com` and `datalazo.net`.
   - Confirm DKIM, SPF, and domain status show green checkmarks.

2. **Inbound Webhook Domain Filtering:**
   - Navigate to [Resend Dashboard → Webhooks](https://resend.com/webhooks).
   - **VRT Webhook:** Edit `https://vrtservices12.com/api/webhooks/resend-inbound` and set its **Domain Filter / Listen to** setting strictly to **`vrtservices12.com`**.
   - **Datalazo Webhook:** Edit `https://crm.datalazo.net/api/webhooks/resend-inbound` and set its **Domain Filter / Listen to** setting strictly to **`datalazo.net`**.

---

## 4. Code & Webhook Protection Safeguards (`app.py`)

In `app.py` (`resend_inbound_webhook`), inbound emails undergo domain validation before reaching default fallback `CUST-0000`:
- If an inbound webhook arrives at `vrtservices12.com` for `@datalazo.net` or another domain, the portal marks it as `IGNORED: Wrong domain` and discards it.
- Unmatched emails belonging to `@vrtservices12.com` route to system fallback customer `CUST-0000`.

---

## 5. Environment Variables

### VRT Services (`vrtservices12.com`)
```env
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=notification@vrtservices12.com
RESEND_TO_EMAIL=luislazober@gmail.com
```

### Datalazo CRM (`crm.datalazo.net`)
```env
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=notification@datalazo.net
RESEND_TO_EMAIL=luislazo@datalazo.net
```
