# Self-Hosted DocuSeal Setup Guide (100% Free & Unlimited)

This guide walks you through deploying **Self-Hosted DocuSeal** on a DigitalOcean Droplet (or any Linux VPS), securing it with SSL, and linking it to VRTServices.

---

## Why Self-Host DocuSeal?

1. **100% Free & Unlimited**: Zero monthly fees, zero document caps, unlimited signers.
2. **IRC § 7216 & IRS Pub 1345 Compliance**: All taxpayer PII remains inside your own private server environment.
3. **Full Data Control**: PDF Audit Trails, IP logs, and SHA-256 hashes are generated locally on your server.

---

## System Requirements

- **Server**: DigitalOcean Droplet / Ubuntu 22.04 LTS (1 vCPU, 1 GB or 2 GB RAM is sufficient).
- **Domain / Subdomain**: e.g., `esign.vrtservices12.com` pointing to your Droplet's public IP address.

---

## Step 1: Install Docker & Docker Compose on your Server

Connect to your server via SSH and install Docker:

```bash
# If using Official Docker repo (Ubuntu 24.04 / Noble):
apt update && apt install -y docker-compose-plugin

# If standard Ubuntu repo:
apt update && apt install -y docker.io docker-compose
systemctl enable --now docker
```

---

## Step 2: Launch DocuSeal Container

Create a directory for DocuSeal and create `docker-compose.yml`:

```bash
mkdir -p /opt/docuseal && cd /opt/docuseal
nano docker-compose.yml
```

Paste the following configuration:

```yaml
version: '3'
services:
  docuseal:
    image: docuseal/docuseal:latest
    container_name: docuseal
    restart: always
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - DATABASE_URL=sqlite3:/data/docuseal.sqlite3
    volumes:
      - ./docuseal_data:/data
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`), then start the container:

```bash
docker-compose up -d
```

DocuSeal is now running locally on port `3000`.

---

## Step 3: Configure Free SSL & Nginx Reverse Proxy

Install Nginx and Certbot for free HTTPS certificates:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create Nginx site configuration:

```bash
sudo nano /etc/nginx/sites-available/docuseal
```

Paste:

```nginx
server {
    server_name esign.vrtservices12.com;  # Your DocuSeal subdomain

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and issue SSL certificate:

```bash
sudo ln -s /etc/nginx/sites-available/docuseal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d esign.vrtservices12.com
```

---

## Step 4: Initial Admin Setup & API Key Creation

1. Open your domain in browser: `https://esign.vrtservices12.com`
2. Complete the initial admin signup (Email & Password).
3. Navigate to **Settings ➔ API** from the left menu (`https://esign.vrtservices12.com/settings/api`).
4. Click **Create API Key** and copy the generated token.
5. Navigate to **Settings ➔ Webhooks**:
   - **Target URL**: `https://vrtservices12.com/api/webhooks/docuseal`
   - **Events**: Select `form.completed` and `submission.completed`.

---

## Step 5: Connect to VRTServices `.env`

Update your `d:\VRTServices\.env` file with your new self-hosted credentials:

```env
DOCUSEAL_API_KEY=your_generated_api_key_here
DOCUSEAL_HOST=https://esign.vrtservices12.com
```

---

## How It Works end-to-end

1. When you click **Send E-Signature Request** in VRTServices (`/management-tools` ➔ `E-Signatures` tab):
   - `app.py` sends a request to `https://esign.vrtservices12.com/submissions`.
2. DocuSeal sends the email invitation to the client or generates the signature link for iframe embed.
3. When the taxpayer signs, your self-hosted DocuSeal instance fires a webhook to `https://vrtservices12.com/api/webhooks/docuseal`.
4. VRTServices automatically downloads the signed PDF + audit trail certificate and stores it in DigitalOcean Spaces (`datalazocrm`) at:
   `${Parent Name}/${Customer Legal Name}/ESignatures/${Document}_Signed.pdf`
5. VRTServices automatically updates `tax_client_signature = TRUE` on the customer's tax checklist.
