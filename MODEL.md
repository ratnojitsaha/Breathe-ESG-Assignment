# Data Model & Architectural Design

This document details the schema and architectural decisions for the Breathe ESG Ingestion Platform.

## 1. Multi-Tenancy Strategy
The platform is built as a **Multi-Tenant SaaS** from the ground up.
- **Tenant Boundary**: The `Company` model acts as the primary isolation boundary.
- **Scoping**: Every operational table—from `DataSource` to `AuditLog`—carries a `company_id`. 
- **Isolation**: API queries are strictly filtered by company ID. In a production environment, this would be reinforced by middleware (e.g., `django-multitenant`) or database-level Row Level Security (RLS) to ensure that Tenant A can never access Tenant B's data.

## 2. Source-of-Truth Tracking (Raw vs. Normalized)
Auditors require proof that the data shown in reports matches the original source. To satisfy this, we use a two-tier storage strategy:
- **`RawRecord`**: Stores the exact, unmodified payload from the source system (SAP, Utility portal, etc.) as a JSON blob. This is the "Evidence."
- **`NormalizedRecord`**: Stores the interpreted, cleaned, and categorized version of that data. This is the "Operational Data."
- **Lineage**: A 1:1 relationship between `NormalizedRecord` and `RawRecord` allows an auditor to click any row in the dashboard and immediately view the original source payload that produced it.

## 3. Scope 1/2/3 Categorization
The platform automatically routes ingested data into the appropriate GHG Protocol categories:
- **Scope 1 (Direct Emissions)**: Captured via the SAP Fuel & Procurement source (e.g., Diesel, Natural Gas).
- **Scope 2 (Indirect Emissions)**: Captured via Utility Electricity sources.
- **Scope 3 (Other Indirect)**: Captured via Corporate Travel (Flights, Hotels, Ground Transport).
The `SourceType` on the `DataSource` model dictates the default Scope categorization, ensuring consistent reporting.

## 4. Unit Normalization Engine
ESG data arrives in a "messy" state: Gallons vs. Liters, MWh vs. kWh, Miles vs. Kilometers.
- **The Mapper**: The `normalization.py` service contains conversion tables (e.g., `FUEL_UNITS_TO_LITERS`).
- **Canonical Units**: All records are converted to a standard unit (e.g., `L`, `kWh`, `km`) before being stored in the `normalized_value` field.
- **Preservation**: The original value and unit are preserved in `original_value` and `original_unit` fields for transparency.

## 5. Audit Trail & History
Every mutation in the system is recorded to ensure accountability.
- **`AuditLog`**: An append-only table that captures every ingestion event and system change. It uses a `before` and `after` JSON snapshot to show exactly what changed.
- **`AnalystReview`**: Every manual decision made by an analyst (Approve/Reject) is tracked with timestamps, actor IDs, and comments.
- **Immutable Logs**: The `AuditLog` model has a overridden `save()` method that prevents updates to existing entries, ensuring the history cannot be tampered with.

## 6. Validation & Flagging (The "Suspicious" Logic)
Data quality is enforced through a deterministic validation service:
- **Errors**: Missing critical data (like units or dates) flags the record as `REJECTED`.
- **Warnings (Suspicious)**: Non-blocking issues—such as a suspiciously high electricity read or an unknown fuel type fallback—flag the record for manual inspection.
- **Analyst Workflow**: These records appear in the "Failed or Suspicious" panel, requiring an analyst to manually approve them before they can be "Audit Locked."

---

## Schema Overview (Simplified)

| Model | Purpose |
| :--- | :--- |
| `Company` | The tenant (e.g., Breathe ESG Assignment). |
| `DataSource` | Configuration for a specific stream (e.g., "SAP MM Export"). |
| `RawUpload` | Metadata for an uploaded file (status, row counts). |
| `RawRecord` | The original source JSON (the Evidence). |
| `NormalizedRecord`| The cleaned activity row (the Operational Data). |
| `ValidationIssue` | Flags for errors or suspicious data. |
| `AuditLog` | Append-only history of all system actions. |
