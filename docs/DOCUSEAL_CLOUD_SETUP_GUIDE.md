# DocuSeal Cloud Setup Guide (SaaS Option A)

This guide walks you through connecting **DocuSeal Cloud** (`https://api.docuseal.com`) to VRTServices.

---

## Step 1: Create a Free DocuSeal Account

1. Go to [docuseal.com](https://www.docuseal.com) and click **Sign Up**.
2. Create your account (Free tier includes **10 documents/month**, Pro tier offers unlimited documents for $15–$35/mo).

---

## Step 2: Get Your DocuSeal Cloud API Key

1. Log in to your DocuSeal dashboard at [docuseal.com/app](https://docuseal.com/app).
2. Go to **Settings ➔ API** from the left navigation menu.
3. Click **Create API Key** (or copy your existing API Token).

---

## Step 3: Configure Webhook Routing in DocuSeal Cloud

1. In your DocuSeal dashboard, go to **Settings ➔ Webhooks**.
2. Click **Add Webhook**:
   - **Target URL**: `https://vrtservices12.com/api/webhooks/docuseal`
   - **Events**: Select `form.completed` and `submission.completed`.
3. Click **Save Webhook**.

---

## Step 4: Add API Key to VRTServices `.env`

Add these lines to your `d:\VRTServices\.env` file:

```env
DOCUSEAL_API_KEY=your_copied_api_key_here
DOCUSEAL_HOST=https://api.docuseal.com
```

---

## How It Works

1. **Send E-Signature Request**:
   - In VRTServices CRM (`/management-tools` ➔ **✍️ E-Signatures** tab), click **🚀 Send E-Signature Request**.
   - Select the customer (Form 8879, Engagement Letter, Tax Organizer).
   - Click **Send**. VRTServices makes an API call to DocuSeal Cloud.
2. **Client Signs Document**:
   - The signer receives an email invitation from DocuSeal or opens the signature link in the CRM modal.
3. **Automatic Cloud Storage & Checklist Sync**:
   - Upon completion, DocuSeal Cloud fires a webhook to `https://vrt-services.com/api/webhooks/docuseal`.
   - VRTServices automatically downloads the signed PDF document + audit certificate and stores it in DigitalOcean Spaces (`datalazocrm`) at:
     `${Parent Name}/${Customer Legal Name}/ESignatures/${Document}_Signed.pdf`
   - VRTServices automatically updates `tax_client_signature = TRUE` on the customer's tax checklist.
