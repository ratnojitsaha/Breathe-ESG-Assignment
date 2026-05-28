# Breathe ESG Ingestion & Analytics Platform

A high-fidelity ESG data orchestration engine designed to transform fragmented enterprise data into audit-ready activity records. This platform implements a robust **Three-Layer Architecture** to ensure data lineage, tenant isolation, and regulatory transparency.

## 🚀 Live Deployment
- **Frontend Dashboard:** [https://breathe-esg-assignment-livid.vercel.app/](https://breathe-esg-assignment-livid.vercel.app/)
- **Backend API:** [https://breathe-esg-assignment-3nq5.onrender.com/api/](https://breathe-esg-assignment-3nq5.onrender.com/api/)
- **Admin Portal:** [https://breathe-esg-assignment-3nq5.onrender.com/admin/](https://esg-ingestion-prototype.onrender.com/admin/)
- **Default Credentials:** `admin` / `admin1234`

---

## 🏗️ Architectural Blueprint

The platform is engineered around three distinct logical layers to ensure scalability and maintainability:

### 1. Core Layer (The Foundation)
Responsible for **Tenant Boundary Enforcement** and reference data.
- **Why**: Multi-tenancy is enforced at the row level via `Company` scoping. This ensures that even in a shared infrastructure, data leakage between organizations is architecturally impossible.
- **Key Models**: `Company`, `DataSource`.

### 2. Ingestion Layer (The Evidence)
Handles raw data preservation and source-specific staging.
- **Why**: Auditors require "immutable evidence." We preserve every source row in source-specific staging tables (e.g., `SapGoodsMovementStaging`) using original field names before any transformation occurs.
- **Key Components**: `parsers.py`, `normalizers/`, and Staging Tables.

### 3. Activity Layer (The Operational Truth)
The final destination for cleaned, normalized, and categorized ESG data.
- **Why**: Provides a unified schema for Scope 1, 2, and 3 reporting regardless of the original source's complexity.
- **Key Models**: `ActivityRecord` (NormalizedRecord), `AuditLog`, `AnalystReview`.

---

## 🛠️ Technical Decisions & Rationale

### IDoc vs. CSV (The Practical Choice)
**Decision**: Ingested SAP data via CSV extracts instead of raw IDoc binary/XML.
**Rationale**: Native IDocs require proprietary SAP middleware (like SAP PI/PO) to be useful. By targeting CSV extracts, we demonstrate the ability to handle **SAP logic** (plant codes, movement types, unit overrides) while keeping the platform accessible for onboarding without the $100k+ overhead of enterprise middleware.

### Per-Record Atomic Transactions
**Decision**: Implemented `@transaction.atomic` at the individual record level rather than the whole file.
**Rationale**: In large-scale ESG ingestion, one bad row shouldn't block 10,000 good ones. Our architecture ensures that valid records are ingested and "Needs Review" flags are raised only for problematic rows, maximizing system uptime.

### PostgreSQL & dj-database-url
**Decision**: Standardized on PostgreSQL with `DATABASE_URL` configuration.
**Rationale**: To support enterprise-grade deployments on platforms like Render/AWS, we moved away from file-based SQLite. This ensures concurrency support and relational integrity for complex audit trails.

---

## 📊 Data Flow: "Source to Audit"
1. **Upload**: User provides a file (SAP CSV, Utility CSV, or Travel JSON).
2. **Stage**: Data is stored in source-specific staging tables with original headers.
3. **Normalize**: Source-specific normalizers (e.g., `sap_normalizer.py`) perform unit conversion and GHG Scope categorization.
4. **Validate**: Deterministic rules flag "Suspicious" data (e.g., usage spikes) or "Failed" data (missing units).
5. **Review**: Analysts approve/reject via the dashboard, creating an immutable **Audit Log**.

---

## 💻 Local Development

### Prerequisites
- Python 3.12+
- Node 22+
- PostgreSQL (Optional, defaults to SQLite)

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo  # Populates sample ESG data
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Deliverables Documentation
For a deeper dive into the methodology, see:
- **[MODEL.md](./MODEL.md)**: Deep dive into the relational schema.
- **[DECISIONS.md](./DECISIONS.md)**: Detailed breakdown of product/engineering choices.
- **[SOURCES.md](./SOURCES.md)**: Research notes on SAP, Utility, and Travel data shapes.
- **[TRADEOFFS.md](./TRADEOFFS.md)**: What we chose not to build and why.
