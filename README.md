# Breathe ESG Ingestion Platform — Prototype

## Live Deployment
- **Dashboard:** [https://esg-ingestion-prototype.vercel.app](https://esg-ingestion-prototype.vercel.app)
- **API Root:** [https://esg-ingestion-prototype.onrender.com/api/](https://esg-ingestion-prototype.onrender.com/api/)
- **Admin Portal:** [https://esg-ingestion-prototype.onrender.com/admin/](https://esg-ingestion-prototype.onrender.com/admin/)
- **Credentials:** `admin` / `admin1234`

## Technical Documentation
Detailed architectural and research notes precede the code:
- **[MODEL.md](./MODEL.md)** — Data model, multi-tenancy, and normalization design.
- **[DECISIONS.md](./DECISIONS.md)** — Ambiguities resolved and technical justifications.
- **[TRADEOFFS.md](./TRADEOFFS.md)** — Deliberate omissions and future-proofing.
- **[SOURCES.md](./SOURCES.md)** — Primary-source research on SAP, Utility, and Travel data.

---

## Overview
This prototype implements three ESG data sources end-to-end: **Ingestion → Normalization → Flagging → Review Dashboard**.

1.  **SAP Fuel & Procurement**: Handles material extracts with plant codes, posting dates, and unit inconsistencies.
2.  **Utility Electricity**: Processes meter-level usage with non-calendar billing cycles.
3.  **Corporate Travel**: Normalizes Concur-style expense JSON into activity-based flight and hotel records.

## Run Locally

### Prerequisites
- Python 3.12+
- Node 22+
- Docker (optional, for PostgreSQL)

### Backend (Terminal 1)
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
- **Dashboard**: `http://localhost:5173`
- **Admin**: `http://localhost:8000/admin/`

---

## Architecture Summary

### Multi-Source Staging
The system utilizes a **Raw-to-Normalized** pattern. Every ingested row is first preserved as a `RawRecord` (storing the original JSON payload) before being processed into a `NormalizedRecord`. This ensures an immutable source of truth for auditors.

### Shared Services vs. Source-Specific Logic
- **Genuinely Shared**: `NormalizedRecord` schema, `AuditLog` events, `AnalystReview` transitions, and the unit normalization engine.
- **Source-Specific**: Custom parsers for SAP (CSV), Utility (CSV), and Travel (JSON). Each parser handles unique field mappings, date formats (SAP `YYYYMMDD` vs. ISO 8601), and validation triggers (e.g., flagging negative quantities or invalid airport codes).

### Audit Chokepoint
All review actions (Approve/Reject) pass through a centralized service that transition statuses and writes append-only `AuditLog` entries in a single database transaction. This ensures that no record can be "Audit Locked" without a clear, traceable history.

### The IDoc Decision
CSV data was used for SAP ingestion because publicly accessible and complete IDoc datasets were not readily available. While IDoc files provide a more realistic SAP enterprise integration format, they typically require SAP-specific middleware and system access. For this prototype, CSV allows for a practical approach to demonstrating complex ingestion and normalization without the overhead of enterprise middleware.
