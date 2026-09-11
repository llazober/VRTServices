# 📘 VRTServices Enterprise Platform — Feature & Module Guide

Welcome to the **VRTServices Enterprise Platform** comprehensive feature and module guide. This document provides a detailed breakdown of all 12 core modules, architectural components, workflows, and integrations built into the application suite.

---

## 🏛️ System Architecture Overview

- **Core Backend Framework**: Python 3.10+ with FastAPI running on Uvicorn.
- **Database Engine**: Multi-schema PostgreSQL (`VRT` database) hosted on DigitalOcean Managed Postgres with connection pooling.
- **Cloud Storage Infrastructure**: DigitalOcean Spaces S3-compatible object storage (`datalazocrm` bucket) with automated customer folder trees (`Customers/<Legal_Name>_<ID>/...`).
- **Email Infrastructure**: Resend API (`notification@vrtservices12.com`) with per-portal webhook routing, custom DKIM/SPF/DMARC verification, and 15-minute inbound email deduplication.
- **E-Signature Suite**: 100% Self-Hosted DocuSeal instance on `https://esign.vrtservices12.com` providing IRS § 7216 compliant e-signature workflows with SHA256 audit trail certificates.

---

## 📑 Table of Contents

1. [Dashboard & Analytics Module](#1-dashboard--analytics-module)
2. [Customer Relationship Management (CRM) & Task Checklist](#2-customer-relationship-management-crm--task-checklist)
3. [DigitalOcean Spaces Cloud Storage Manager](#3-digitalocean-spaces-cloud-storage-manager)
4. [Self-Hosted E-Signature & IRS § 7216 Compliance Module](#4-self-hosted-e-signature--irs--7216-compliance-module)
5. [AI Knowledge Base & RAG Vector Search Module](#5-ai-knowledge-base--rag-vector-search-module)
6. [Check OCR Extraction & GL Account Matching Engine](#6-check-ocr-extraction--gl-account-matching-engine)
7. [Compliance Calendar & Tax Deadline Engine](#7-compliance-calendar--tax-deadline-engine)
8. [Automated Billing & Recurring Invoice Module](#8-automated-billing--recurring-invoice-module)
9. [Unified Communications & Inbound Email Inbox](#9-unified-communications--inbound-email-inbox)
10. [QuickBooks Online (QBO) Integration](#10-quickbooks-online-qbo-integration)
11. [Tax Team & User Management Module](#11-tax-team--user-management-module)
12. [Audit Logging, Debugging & System Security](#12-audit-logging-debugging--system-security)

---

## 1. Dashboard & Analytics Module

**Primary Routes**: `/dashboard`, `/api/dashboard/pending-tasks`

The **Dashboard** serves as the central command center for firm operations, offering real-time visibility into active client status, financial metrics, and pending tax preparation tasks.

### Key Features:
- **Executive KPI Cards**: Real-time counters for Active Clients, Pending Tax Returns, Outstanding Invoice Totals, and Pending E-Signature Requests.
- **Pending Tasks Widget**: Aggregates tax client checklist steps needing attention across all assigned customers.
- **Global Search Bar**: Instant search across clients, invoice numbers, e-signature requests, and compliance events.
- **Compliance Status Badges**: Quick visual indicators for client tax standing (Compliant, Upcoming Deadline, Overdue).

---

## 2. Customer Relationship Management (CRM) & Task Checklist

**Primary Routes**: `/customers`, `/api/customers`, `/api/customers/{id}/checklist`

The **CRM Module** maintains client entity records, parent company structures, tax team assignments, and the 4-Step Tax Preparation Pipeline.

### Key Features:
- **Client Profile Management**: Maintains Legal Name, Parent Company, EIN/SSN, Entity Type (S-Corp, C-Corp, Partnership, Individual), Contact Email, and Tax Preparer/Reviewer assignments.
- **4-Step Tax Preparation Checklist Pipeline**:
  - **Step 1 — Client Documents Received**: Tracks intake of W-2s, 1099s, K-1s, and financial statements.
  - **Step 2 — Tax Return Prepared**: Indicates tax return calculation completion by assigned preparer.
  - **Step 3 — Quality Control / Review**: Manager review and approval.
  - **Step 4 — Tax Client Signature**: Automatically updates to `TRUE` when an e-signature request is completed via DocuSeal webhook.
- **Two-Way Synchronization**: Toggling checklist Step 4 automatically updates the compliance calendar status and vice versa.
- **Period Reopening & Multi-Year Archiving**: Reopen past tax years for amended returns while preserving historical audit records.

---

## 3. DigitalOcean Spaces Cloud Storage Manager

**Primary Routes**: `/api/customers/{id}/storage/...`, `/api/storage/view-pdf`, `/api/storage/download`

A fully featured, S3-backed cloud file manager integrated directly into each customer profile.

### Key Features:
- **Automated Root Folder Initialization**: Automatically creates `/Customers/<Legal_Name>_<ID>/` with subfolders (`/ESignatures`, `/Tax_Returns`, `/Financial_Statements`, `/Invoices`).
- **File & Folder Operations**: Create folders (`mkdir`), upload files, rename, move, and soft/hard delete.
- **Secure Inline PDF Viewer**: Stream PDF documents safely using `/api/storage/view-pdf` with signed S3 URLs.
- **Direct Downloads**: Download audit certificates, tax returns, and client attachments securely.

---

## 4. Self-Hosted E-Signature & IRS § 7216 Compliance Module

**Primary Routes**: `/esign/{request_id}`, `/esign/completed`, `/api/esignature/...`, `/api/webhooks/docuseal`

A 100% self-hosted e-signature solution running on `https://esign.vrtservices12.com` providing full compliance with IRS § 7216 tax privacy regulations without third-party cloud data exposure.

### Key Features:
- **Smart Template Matching**: Automatically matches signature requests to templates created in DocuSeal by keyword:
  - `Form 8879` ➔ Matches `8879` templates.
  - `IRC § 7216 Consent` ➔ Matches `7216` or `Consent` templates.
  - `Tax Organizer` ➔ Matches `Organizer` templates.
  - `Engagement Letter` ➔ Matches `Engagement` templates.
- **Direct Redirect Flow**: Direct 307 redirect to `https://esign.vrtservices12.com/s/{slug}` to eliminate browser iframe connection refusals (`SAMEORIGIN` blocks) and mobile touch issues.
- **Post-Signature Thank You & Redirect**: Upon signature completion, automatically redirects signers to `/esign/completed` with a button to return to the VRT Services portal.
- **Automated S3 Archiving**: Webhooks catch `form.completed` events, download the signed PDF and official SHA256 Audit Trail Certificate PDF, upload them to DigitalOcean Spaces, and mark the customer's checklist complete.

---

## 5. AI Knowledge Base & RAG Vector Search Module

**Primary Routes**: `/api/kb/documents`, `/api/kb/upload`, `/api/kb/query`, `/api/history/learn`

An AI-powered Retrieval-Augmented Generation (RAG) search engine built to answer complex tax preparation, IRS regulation, and firm-specific workflow queries.

### Key Features:
- **Document Ingestion**: Upload internal standard operating procedures (SOPs), IRS guides, and firm policies.
- **Text Chunking & Vector Search**: Chunks text and queries vector embeddings to surface exact relevant paragraphs.
- **Feedback & Learning Loop**: Store corrections via `/api/history/learn` so the AI assistant adapts to firm preferences over time.

---

## 6. Check OCR Extraction & GL Account Matching Engine

**Primary Routes**: `/ocr`, `/extractor`, `/process-checks-from-do`, `matching_engine.py`

An automated document processing module designed to parse scanned check images, extract transaction metadata, and match items against the General Ledger (GL).

### Key Features:
- **OCR Text & Numeric Extraction**: Parses scanned check images to extract Payer Name, Payee Name, Date, Check Number, Amount, and Memo.
- **General Ledger (GL) Matching**: Matches extracted payee names against the client’s Chart of Accounts (COA) and historical transaction history.
- **Batch Processing**: Batch process check images stored in DigitalOcean Spaces (`/process-checks-from-do`).

---

## 7. Compliance Calendar & Tax Deadline Engine

**Primary Routes**: `/calendar`, `/compliance`, `/api/compliance/events`, `/api/compliance/generate-preset-all`

A comprehensive compliance engine tracking federal, state, and local tax deadlines for all client entity types.

### Key Features:
- **Preset Deadline Generator**: Automatically generates annual tax deadlines based on entity type:
  - **Individual (1040)**: Federal April 15, Q1-Q4 Estimated Taxes.
  - **S-Corporation (1120-S)**: March 15 Return, Franchise Tax.
  - **Partnership (1065)**: March 15 Return.
  - **C-Corporation (1120)**: April 15 Return.
  - **Payroll Taxes**: Form 941 (Quarterly), Form 940 (Annual).
- **Interactive Calendar & Event Status**: Update event status (Pending, Completed, Waived, Extension Filed).
- **Automated Two-Way Sync**: Completing an e-signature automatically updates the corresponding compliance calendar event.

---

## 8. Automated Billing & Recurring Invoice Module

**Primary Routes**: `/billing`, `/invoices`, `/api/billing/schedules`, `/api/billing/invoices`

A specialized billing system for accounting firms supporting fixed fee schedules, recurring billing, catch-up billing, and invoice email dispatch.

### Key Features:
- **Flexible Billing Cycles**: Supports Monthly, Quarterly, Annual, and One-Time billing schedules.
- **Catch-Up Billing Math**: Calculates retroactive prorated fees for clients joining mid-cycle.
- **Invoice Generation & Resend Email Dispatch**: Generates clean invoice records and dispatches HTML email notifications via Resend API.
- **Invoice Status Lifecycle**: Track status across `Draft`, `Sent`, `Paid`, and `Overdue`.

---

## 9. Unified Communications & Inbound Email Inbox

**Primary Routes**: `/api/communications/all-inbound`, `/api/communications/unread-summary`, `/api/webhook/resend-inbound`

A centralized email communication inbox connecting inbound emails from clients directly to their customer profile.

### Key Features:
- **Inbound Webhook Processor**: Receives inbound client emails sent to `notification@vrtservices12.com` via Resend webhooks.
- **Attachment Extraction to S3**: Automatically extracts email attachments and saves them under the client's `/Inbound_Email_Attachments` folder in DigitalOcean Spaces.
- **Deduplication Engine**: Uses a 15-minute deduplication window and `email_id` preservation to prevent duplicate receipts.
- **Unread Counter & Notification Badges**: Real-time unread email indicators in the top bar navigation.

---

## 10. QuickBooks Online (QBO) Integration

**Primary Routes**: `/auth/qbo/login`, `/auth/qbo/callback`, `/api/qbo/status`, `/api/qbo/export`

OAuth2 integration connecting VRTServices to QuickBooks Online for seamless financial data synchronization.

### Key Features:
- **OAuth2 Authentication**: Secure connection flow supporting Sandbox and Production QBO environments.
- **Chart of Accounts Sync**: Import client COA from QuickBooks directly into VRTServices.
- **Invoice & Transaction Export**: Push invoices and transaction records created in VRTServices directly into QBO.

---

## 11. Tax Team & User Management Module

**Primary Routes**: `/management-tools`, `/api/tax-team`

User management and team assignment tools to structure workflow responsibilities across the firm.

### Key Features:
- **Role-Based Access Control (RBAC)**: Support for Administrator, Tax Manager, Tax Preparer, and Quality Control Reviewer roles.
- **Team Assignment**: Assign primary preparers and reviewers to specific client accounts.
- **Performance & Workload Tracking**: Track task completion velocity across team members.

---

## 12. Audit Logging, Debugging & System Security

**Primary Routes**: `/api/audit-logs`, `/api/debug/docuseal-config`, `/health`

Built-in observability, compliance logging, and system health checks.

### Key Features:
- **Immutable Audit Trail**: Records key system actions (user logins, document deletions, invoice updates, e-signature requests).
- **Exportable Logs**: Export audit trails in CSV format for compliance reporting (`/api/audit-logs/export`).
- **Live Health & Configuration Diagnostics**: Instant inspection endpoints (`/health`, `/api/debug/docuseal-config`, `/api/debug/inbound-status`).

---

## 📌 Technical Summary

| Component | Technology / Service |
| :--- | :--- |
| **Language & Web Server** | Python 3.10+, FastAPI, Uvicorn |
| **Primary Database** | PostgreSQL on DigitalOcean (`VRT` database) |
| **Object Storage** | DigitalOcean Spaces S3 (`datalazocrm`) |
| **E-Signatures** | DocuSeal Self-Hosted (`https://esign.vrtservices12.com`) |
| **Outbound & Inbound Email** | Resend API (`notification@vrtservices12.com`) |
| **Accounting Integration** | QuickBooks Online (QBO) OAuth2 API |
