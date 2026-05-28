# Data Model

## Core Tables

`Company` is the tenant boundary. Every operational record, issue, upload, and audit log carries `company_id` so API filters can keep data scoped.

`DataSource` represents a configured source for a company: SAP fuel/procurement, utility electricity, or corporate travel.

`RawUpload` stores upload metadata: source type, filename, uploader, timestamp, processing status, and record counts.

`RawRecord` stores each unprocessed source row as JSON. This is intentionally separate from normalized data so auditors can compare the exact ingested payload with the normalized result.

`NormalizedRecord` is the canonical activity row. It stores activity category, Scope 1/2/3 category, original and normalized units/values, dates, facility/vendor context, review status, audit lock state, and a one-to-one reference to `RawRecord`.

`ValidationIssue` stores deterministic validation results against raw and normalized records. Warnings and errors are both visible to analysts.

`AnalystReview` stores review decisions over time.

`AuditLog` stores append-only ingestion and review events with before/after JSON snapshots.

## Relationships

- `Company` has many `DataSource`, `RawUpload`, `RawRecord`, `NormalizedRecord`, `ValidationIssue`, and `AuditLog`.
- `RawUpload` has many `RawRecord`.
- `RawRecord` has one `NormalizedRecord`.
- `RawRecord` and `NormalizedRecord` both link to `ValidationIssue`.
- `NormalizedRecord` has many `AnalystReview`.

## Normalization Flow

1. Analyst uploads a file against a configured `DataSource`.
2. A `RawUpload` is created.
3. Source-specific parser reads each source row.
4. Each row is stored as `RawRecord.original_payload`.
5. The parser maps source fields into a `NormalizedRecord`.
6. Validation rules create `ValidationIssue` rows.
7. Records with issues become `NEEDS_REVIEW`; clean records remain `PENDING`.
8. Analyst approves or rejects. Approval sets `locked_for_audit = true`.

## Auditability Strategy

Raw payloads are never overwritten. Normalized rows point back to raw records using a one-to-one relationship and a source reference from the original system where available. Review changes create `AnalystReview` and `AuditLog` entries. `AuditLog.save()` rejects updates to existing rows.

## Multi-Tenancy Strategy

This prototype uses row-level tenancy through `Company` foreign keys. In production, this would be backed by authentication, authorization, query scoping middleware, and database constraints or row-level security for stronger isolation.

## Source Lineage Strategy

Lineage is preserved through:

- `RawUpload`: file-level provenance.
- `RawRecord`: row-level source payload.
- `NormalizedRecord.raw_record`: canonical-to-raw link.
- `source_record_reference`: source document, bill, expense, or fallback row reference.
- `AuditLog`: action history.
