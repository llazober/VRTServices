# Compliance Calendar Module - Technical Specification & Implementation Plan

This document outlines the complete architectural design and step-by-step technical plan for integrating a **Compliance Calendar Module** into VRT Services CRM (`d:\VRTServices`).

---

## 1. Core Idea & Feature Overview

Every client account in VRTServices (`customer` table) has recurring and one-off tax & regulatory filing deadlines:
- 📊 **Sales Tax Filing** (Monthly, Quarterly, Annual)
- 💼 **Payroll Tax Deposits & Returns** (Form 941, 940, State unemployment, Semi-weekly/Monthly deposits)
- 🏛️ **Quarterly Estimated Taxes** (Form 1040-ES, 1120-W)
- 📑 **Annual Corporate & Individual Tax Returns** (Form 1120, 1120-S, 1065, 1040)
- ✉️ **Information Returns** (1099-NEC, 1099-MISC, W-2 / W-3)
- 🏢 **Franchise Tax & Annual Corporate Reports** (State filing deadlines)
- 📈 **Bookkeeping Cycles** (Monthly Close, Bank Reconciliations, Financial Statements)
- 📌 **Custom Firm Deadlines** (Firm-specific tasks or client requests)

---

## 2. Design & Architecture Decisions

1. **Preset Generation Mode**:
   - Preset compliance schedule generation will be **manual via button click** (`⚡ Generate Preset Compliance Schedule`) inside the Compliance Calendar screen or Customer details.
2. **Notification Channel**:
   - Automated Resend email alerts (`RESEND_API_KEY`) will notify internal **Assigned Tax Preps** (`TaxTeam`) 7 days, 3 days, and day-of upcoming or overdue deadlines.

---

## 3. Database Schema (`app.py`)

```sql
CREATE TABLE IF NOT EXISTS compliance_calendar_events (
    id                  BIGSERIAL PRIMARY KEY,
    customer_id         BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    category            VARCHAR(50) NOT NULL, -- 'Sales Tax', 'Payroll Tax', 'Estimated Tax', 'Corporate Tax', '1099/W2', 'Franchise Tax', 'Bookkeeping Close', 'Custom'
    title               VARCHAR(250) NOT NULL,
    description         TEXT,
    jurisdiction        VARCHAR(100) DEFAULT 'Federal', -- e.g. 'Federal', 'Florida', 'California', 'Local'
    due_date            DATE NOT NULL,
    frequency           VARCHAR(30) NOT NULL DEFAULT 'One-Off', -- 'One-Off', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual'
    assigned_tax_prep   VARCHAR(100), -- References TaxTeam.name
    status              VARCHAR(30) NOT NULL DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Completed', 'Overdue', 'Waived'
    reminder_days_prior INT NOT NULL DEFAULT 7,
    completed_at        TIMESTAMP,
    completed_by        VARCHAR(100),
    auto_generated      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_compliance_events_customer_id ON compliance_calendar_events (customer_id);
CREATE INDEX IF NOT EXISTS idx_compliance_events_due_date ON compliance_calendar_events (due_date);
CREATE INDEX IF NOT EXISTS idx_compliance_events_status ON compliance_calendar_events (status);
CREATE INDEX IF NOT EXISTS idx_compliance_events_tax_prep ON compliance_calendar_events (assigned_tax_prep);
```

---

## 4. Backend API Endpoints (`app.py`)

- `GET /compliance`: Render the main Compliance Calendar page tab.
- `GET /api/compliance/events`: Fetch compliance deadlines with filtering by `customer_id`, `category`, `status`, `assigned_tax_prep`, `month`, and `year`.
- `POST /api/compliance/events`: Create a new compliance deadline (one-off or recurring).
- `PUT /api/compliance/events/{event_id}`: Modify deadline details, assigned tax prep, or due date.
- `DELETE /api/compliance/events/{event_id}`: Remove a compliance deadline.
- `POST /api/compliance/events/{event_id}/status`: Toggle status (`Completed`, `Pending`, `In Progress`, `Waived`) with audit logging.
- `POST /api/compliance/generate-preset/{customer_id}`: Manually generate standard compliance preset schedule for a client via button click.

---

## 5. UI Integration (`templates/dashboard.html`)

1. **Left Sidebar Link**:
   - Add **Compliance Calendar** navigation link under **CRM Modules** with calendar icon 📅 and badge `TAX`.
2. **Dashboard Views**:
   - **Header KPI Cards**: Overdue Deadlines, Due Next 7 Days, Pending This Month, Completed Metric %.
   - **Dual Views**: Monthly Interactive Calendar Grid + High-Density Enterprise Datatable.
   - **Filters Toolbar**: Customer, Category, Assigned Tax Prep, Status, Date Picker.
   - **Action Buttons**: `➕ Add Deadline` and `⚡ Generate Preset Compliance Schedule`.
3. **Customer Workload Integration**:
   - Display pending compliance deadlines on the main **Customer Workload Pending Tasks** table and Customer Profile modal.

---

## 6. Git Status & Verification Plan
- Compile Python: `python -m py_compile app.py`
- Test API endpoints and table creation.
- Commit to git on `main` branch.
