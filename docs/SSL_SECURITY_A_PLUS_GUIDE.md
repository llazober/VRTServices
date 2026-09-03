# 🛡️ SSL/TLS Security & Cloudflare "A+" Grade Upgrade Guide

Use this guide whenever you launch or configure a new website to ensure high security, privacy compliance, and achieve an **A+ Rating** on [Qualys SSL Labs](https://www.ssllabs.com/ssltest/) and [SecurityHeaders.com](https://securityheaders.com/).

---

## ☁️ Step 1: Cloudflare Dashboard Configuration Checklist

When your domain is proxied through Cloudflare (Orange Cloud enabled), configure these 4 key settings:

### 1. Set Minimum TLS Version to 1.2
- **Path**: **SSL/TLS** $\rightarrow$ **Edge Certificates**
- **Setting**: **Minimum TLS Version** = `TLS 1.2`
- *Why*: Disables deprecated and vulnerable TLS 1.0 & TLS 1.1 protocols.

### 2. Enable HTTP Strict Transport Security (HSTS)
- **Path**: **SSL/TLS** $\rightarrow$ **Edge Certificates** $\rightarrow$ **HTTP Strict Transport Security (HSTS)**
- **Click**: **Enable HSTS**
- **Configure**:
  - **Max-Age Header**: `12 months (31536000 seconds)`
  - **Include Subdomains**: `On`
  - **Preload**: `On`
  - **No-Sniff Header**: `On`
- *Why*: Forces all browsers to communicate strictly over encrypted HTTPS connections.

### 3. Enable TLS 1.3
- **Path**: **SSL/TLS** $\rightarrow$ **Edge Certificates**
- **Setting**: **TLS 1.3** = `Enabled`
- *Why*: Provides faster handshake performance and state-of-the-art encryption algorithms.

### 4. Enforce Always Use HTTPS & Automatic HTTPS Rewrites
- **Path**: **SSL/TLS** $\rightarrow$ **Edge Certificates**
- **Settings**:
  - **Always Use HTTPS**: `On`
  - **Automatic HTTPS Rewrites**: `On`

---

## 💻 Step 2: Backend Security Headers Code Snippets

Add HTTP security headers to your web application backend so that all direct and proxied responses remain protected.

### 🐍 Python (FastAPI / Starlette)
```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self' https: data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: blob: https:; font-src 'self' https: data:; connect-src 'self' https:;"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response
```

### 🐍 Python (Flask)
```python
@app.after_request
def add_security_headers(response):
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 🟢 Node.js (Express with Helmet)
```javascript
const express = require('express');
const helmet = require('helmet');
const app = express();

app.use(helmet({
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
```

### 🌐 Nginx Configuration (`/etc/nginx/sites-available/default`)
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

---

## 🔍 Step 3: Verification Tools & Command Line Testing

After applying the configuration, test your site using these tools:

1. **Qualys SSL Labs**: `https://www.ssllabs.com/ssltest/analyze.html?d=YOURDOMAIN.COM`
2. **Security Headers Rating**: `https://securityheaders.com/?q=YOURDOMAIN.COM`

### Quick Terminal Command Test:
```bash
curl -s -D - https://YOURDOMAIN.COM -o /dev/null
```
Look for:
- `strict-transport-security: max-age=31536000; includeSubDomains; preload`
- `x-content-type-options: nosniff`
- `x-frame-options: SAMEORIGIN`
