# Resend Custom Domains & Multi-Portal Email Routing Setup (Method 1)

## Overview
This guide documents **Method 1** for configuring isolated custom domain email routing between multiple portals (e.g., `vrtservices12.com` and `datalazo.net`) using Resend and Cloudflare DNS.

---

## 1. Cloudflare DNS Configuration

### A. VRT Services Domain (`vrtservices12.com`)
- **DKIM (TXT):**
  - Name: `resend._domainkey.vrtservices12.com`
  - Value: Resend DKIM public key
- **SPF (TXT):**
  - Name: `vrtservices12.com`
  - Value: `"v=spf1 include:spf.efwd.registrar-servers.com include:resend.com ~all"`
- **DMARC (TXT):**
  - Name: `_dmarc.vrtservices12.com`
  - Value: `"v=DMARC1; p=none; rua=mailto:..."`

### B. Datalazo CRM Domain (`datalazo.net`)
- **DKIM (TXT):**
  - Name: `resend._domainkey.datalazo.net`
  - Value: Resend DKIM public key
- **SPF (TXT):**
  - Name: `datalazo.net`
  - Value: `"v=spf1 include:spf.privateemail.com include:resend.com ~all"`
- **DMARC (TXT):**
  - Name: `_dmarc.datalazo.net`
  - Value: `"v=DMARC1; p=none; rua=mailto:..."`

---

## 2. Resend Dashboard Verification & Webhook Binding

1. **Verify Domains:**
   - Navigate to [Resend Dashboard → Domains](https://resend.com/domains).
   - Click **Verify** on both `vrtservices12.com` and `datalazo.net`.

2. **Inbound Webhook Assignments:**
   - Navigate to [Resend Dashboard → Webhooks](https://resend.com/webhooks).
   - **VRT Webhook:** Point `https://vrtservices12.com/api/webhooks/resend-inbound` to the `vrtservices12.com` domain.
   - **Datalazo Webhook:** Point `https://crm.datalazo.net/api/webhooks/resend-inbound` to the `datalazo.net` domain.

---

## 3. Environment Variables

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
