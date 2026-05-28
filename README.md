# Breathe ESG Ingestion Prototype

A Django REST Framework + React/Vite prototype for enterprise ESG activity-data ingestion, normalization, analyst review, and audit locking.

## What It Does

- Upload SAP fuel/procurement CSV, utility electricity CSV, or corporate travel JSON.
- Preserve every raw source row as JSON before normalization.
- Normalize source rows into a shared activity schema with Scope 1/2/3 categorization.
- Flag validation errors and warnings for analyst review.
- Approve records into an audit-locked state.
- Record ingestion and review actions in append-only audit logs.

## Run Locally With Docker

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api/`

The backend container runs migrations and seeds `Rhein Industries AG` with three data sources.

## Manual Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Local development uses SQLite by default, so Docker/PostgreSQL is not required. To use PostgreSQL for deployment, set `DATABASE_ENGINE=postgres` and the `POSTGRES_*` variables.

## Manual Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Sample Files

Use files in `samples/`:

- `sap_fuel_export.csv`
- `utility_electricity_export.csv`
- `corporate_travel_concur.json`

In the frontend, open the `Ingest` tab and use the matching upload lane:

- SAP fuel/procurement accepts CSV only.
- Utility electricity accepts CSV only.
- Corporate travel accepts JSON only.

Each upload is preserved as raw source rows, normalized immediately, and routed to analyst review before audit reporting.

## Documentation

- `MODEL.md`: schema, lineage, multi-tenancy, normalization, auditability.
- `DECISIONS.md`: assumptions and ambiguity resolution.
- `TRADEOFFS.md`: deliberately omitted features.
- `SOURCES.md`: source-format research assumptions.
- `docs/API.md`: endpoint summary.
