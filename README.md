# Breathe ESG Assignment

## Live Deployment

**Frontend:** https://breathe-esg-assignment-livid.vercel.app/

**Backend API:** https://breathe-esg-assignment-3nq5.onrender.com/

---

## Overview

This project is an ESG data ingestion and visualization platform built using React, Django, and Django REST Framework. The system allows ingestion, processing, and visualization of ESG-related organizational data through a responsive dashboard interface.

The application demonstrates:

* ESG data ingestion and processing
* Data normalization and validation
* Interactive dashboard visualization
* REST API integration
* Full-stack deployment using Vercel and Render

---

## Technology Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS

### Backend

* Django
* Django REST Framework

### Deployment

* Vercel (Frontend)
* Render (Backend)

---

## Architecture

The application follows a client-server architecture:

React Frontend → Django REST API → Data Processing Layer

The frontend consumes REST endpoints exposed by the Django backend and renders ESG metrics, summaries, and company-related information.

---

## Data Source Decision

CSV data was used for ingestion because publicly accessible and complete SAP IDoc datasets were not readily available.

While IDoc files provide a more realistic SAP enterprise integration format, they generally require SAP-specific middleware, integration utilities, and system access for proper processing and transformation. For the scope of this assignment, CSV data provided a practical approach for demonstrating ingestion, validation, normalization, and visualization workflows without the overhead of enterprise SAP infrastructure.

---
## Architecture Summary

### Multi-Source Staging
The system utilizes a **Raw-to-Normalized** pattern. Every ingested row is first preserved as a `RawRecord` (storing the original JSON payload) before being processed into a `NormalizedRecord`. This ensures an immutable source of truth for auditors.

### Shared Services vs. Source-Specific Logic
- **Genuinely Shared**: `NormalizedRecord` schema, `AuditLog` events, `AnalystReview` transitions, and the unit normalization engine.
- **Source-Specific**: Custom parsers for SAP (CSV), Utility (CSV), and Travel (JSON). Each parser handles unique field mappings, date formats (SAP `YYYYMMDD` vs. ISO 8601), and validation triggers (e.g., flagging negative quantities or invalid airport codes).

### Audit Chokepoint
All review actions (Approve/Reject) pass through a centralized service that transition statuses and writes append-only `AuditLog` entries in a single database transaction. This ensures that no record can be "Audit Locked" without a clear, traceable history.

### The IDoc vs CSV Decision
CSV data was used for SAP ingestion because publicly accessible and complete IDoc datasets were not readily available. While IDoc files provide a more realistic SAP enterprise integration format, they typically require SAP-specific middleware and system access. For this prototype, CSV allows for a practical approach to demonstrating complex ingestion and normalization without the overhead of enterprise middleware.


---

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:
http://localhost:5173

Backend:
http://localhost:8000

```
```


