# Billing & Recurring Invoicing Module Guide

This document serves as the comprehensive architectural and operational reference for the **Billing & Recurring Invoicing Module** in VRTServices.

---

## 1. Module Overview

The Billing & Recurring Invoicing Module manages contract billing, client subscriptions, recurring schedule automation, manual invoice generation, professional HTML rendering, Resend email dispatch, and financial KPI analytics.

---

## 2. Database Schema

The module relies on two core tables in PostgreSQL:

### A. `billing_schedules` (Subscriptions & Contracts)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Internal schedule identifier |
| `customer_id` | `VARCHAR(50)` | Customer Reference Code (e.g. `CUST-4059`) |
| `frequency` | `VARCHAR(20)` | `MONTHLY`, `QUARTERLY`, or `ANNUALLY` |
| `amount` | `NUMERIC(10, 2)` | Billable amount per cycle |
| `description` | `TEXT` | Subscription details (e.g., *"Virtual Office Plan"*) |
| `next_bill_date` | `DATE` | Scheduled date for next automated invoice generation |
| `is_active` | `BOOLEAN` | Active subscription flag |
| `created_at` | `TIMESTAMP` | Record creation timestamp |

### B. `billing_invoices` (Invoices & Payments)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Internal invoice identifier |
| `invoice_number` | `VARCHAR(50) UNIQUE` | Formatted invoice ID (e.g., `INV-2026-001001`) |
| `customer_id` | `VARCHAR(50)` | Associated Customer ID |
| `schedule_id` | `INTEGER` | Associated schedule ID (or `NULL` if manual) |
| `issue_date` | `DATE` | Invoice issue date |
| `due_date` | `DATE` | Payment due date |
| `subtotal` | `NUMERIC(10, 2)` | Base item sum |
| `tax` | `NUMERIC(10, 2)` | Tax amount |
| `discount` | `NUMERIC(10, 2)` | Applied discount |
| `total_amount` | `NUMERIC(10, 2)` | Final billable amount |
| `status` | `VARCHAR(20)` | `UNPAID`, `PAID`, `OVERDUE`, `CANCELLED` |
| `items_json` | `JSONB` / `TEXT` | Line item details array |
| `sent_at` | `TIMESTAMP` | Timestamp when Resend email was sent |
| `paid_at` | `TIMESTAMP` | Timestamp when marked as paid |
| `created_at` | `TIMESTAMP` | Invoice record creation timestamp |

---

## 3. Step-by-Step Billing Workflow

```
[ Recurring Schedule ] ────(Scheduler / Run)────► [ Invoice Created (UNPAID) ]
                                                               │
                                                 ┌─────────────┴─────────────┐
                                                 ▼                           ▼
                                          [ View HTML / Print ]       [ Resend Email Outbound ]
                                                                             │
                                                                             ▼
                                                                  [ Payment Received ]
                                                                             │
                                                                             ▼
                                                                  [ Status Updated: PAID ]
                                                                             │
                                                                             ▼
                                                                 [ MRR / KPI Dash Updated ]
```

### Step 1: Schedule / Subscription Setup
1. From the dashboard (**Billing & Invoices** tab), click **+ New Recurring Schedule**.
2. Input Customer ID, Frequency (`MONTHLY`, `QUARTERLY`, `ANNUALLY`), amount, start date, and description.
3. Posted to `/api/billing/schedules`. The system sets `next_bill_date` based on the specified start date.

### Step 2: Invoice Generation

#### A. Automated Scheduler (`/api/billing/run-scheduler`)
- Triggered periodically via background job or HTTP GET/POST to `/api/billing/run-scheduler`.
- Queries all active schedules (`is_active = TRUE`) where `next_bill_date <= CURRENT_DATE`.
- Creates a new `UNPAID` invoice record in `billing_invoices`.
- Advances `next_bill_date` automatically based on the schedule's frequency.
- Sends an outbound invoice email via Resend to the customer's email address.

#### B. Manual Invoice Creation
- Click **+ Create Manual Invoice** on the dashboard.
- Provide custom line items, subtotal, tax, discount, issue date, and due date.
- Saved via POST to `/api/billing/invoices`.

### Step 3: Interactive HTML Rendering & PDF Print
- Clicking **View** on an invoice opens a responsive modal populated by `/api/billing/invoices/{id}/view`.
- Features corporate logo, customer information, line items, breakdown, tax calculations, and payment terms.
- Implements CSS `@media print` rules allowing direct one-click PDF generation via standard browser print (`Ctrl+P` / `Cmd+P`).

### Step 4: Outbound Email Dispatch (Resend)
- Clicking **Send Email** calls `/api/billing/invoices/{id}/send`.
- Renders an itemized HTML email layout and dispatches it using Resend API.
- Cleans recipient email addresses to adhere to domain security filters.
- Sets `sent_at = NOW()` upon successful dispatch.

### Step 5: Status Lifecycle Management
- **`UNPAID`**: Initial status upon creation.
- **`PAID`**: Set via `/api/billing/invoices/{id}/status` when payment is received; sets `paid_at = NOW()`.
- **`OVERDUE`**: Automatically categorized when `CURRENT_DATE > due_date` for unpaid invoices.
- **`CANCELLED`**: Marked when an invoice is voided.

### Step 6: KPI Metrics & Dashboard Financial Analytics
The backend endpoint `/api/billing/overview` computes:
- **MRR (Monthly Recurring Revenue)**: Sum of all active recurring subscription schedules normalized to a monthly value (`MONTHLY` * 1, `QUARTERLY` / 3, `ANNUALLY` / 12).
- **Active Subscribers**: Unique count of customers with active billing schedules.
- **Total Revenue Collected**: Sum of `total_amount` across all `PAID` invoices.
- **Outstanding Balance**: Sum of `total_amount` across all `UNPAID` and `OVERDUE` invoices.

---

## 4. API Endpoints Reference

| Route | Method | Description |
| :--- | :--- | :--- |
| `/api/billing/overview` | `GET` | Returns financial KPI summary (MRR, revenue, active subscribers, unpaid totals) |
| `/api/billing/schedules` | `GET` | Lists all recurring subscription schedules |
| `/api/billing/schedules` | `POST` | Creates a new recurring billing schedule |
| `/api/billing/schedules/{id}` | `DELETE` | Deactivates or removes a recurring schedule |
| `/api/billing/invoices` | `GET` | Lists invoices with optional filters (`status`, `customer_id`) |
| `/api/billing/invoices` | `POST` | Manually creates an invoice |
| `/api/billing/invoices/{id}/send` | `POST` | Dispatches invoice via Resend email |
| `/api/billing/invoices/{id}/status` | `POST` | Updates invoice status (`PAID`, `CANCELLED`, `UNPAID`) |
| `/api/billing/invoices/{id}/view` | `GET` | Returns printable HTML invoice page |
| `/api/billing/invoices/{id}` | `DELETE` | Deletes an invoice record |
| `/api/billing/run-scheduler` | `GET/POST` | Executes automated schedule processing & invoice generation |

---

## 5. Source Code References

- Backend Logic & API Routes: [app.py](file:///d:/VRTServices/app.py)
- Frontend UI & JS Controller: [templates/dashboard.html](file:///d:/VRTServices/templates/dashboard.html)
- Custom Domain & Resend Email Guide: [docs/RESEND_CUSTOM_DOMAINS_GUIDE.md](file:///d:/VRTServices/docs/RESEND_CUSTOM_DOMAINS_GUIDE.md)
