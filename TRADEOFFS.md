# Tradeoffs

## Omitted: OCR/PDF Ingestion

Utility PDFs are realistic but OCR adds parsing uncertainty and infrastructure complexity. CSV was chosen to focus on clean lineage and review workflow.

## Omitted: Distributed Async Pipeline

Large production uploads should run through Celery, queues, object storage, and retry handling. This prototype processes synchronously to keep behavior easy to inspect.

## Omitted: Emissions Factor Engine

The app normalizes activity data but does not calculate CO2e. Factor selection requires geography, time period, methodology, and versioning decisions that deserve a separate design.

## Omitted: SSO And Role-Based Auth

Enterprise auth is important, but the prototype focuses on the ingestion model. The schema leaves `uploaded_by`, `reviewed_by`, and `actor` hooks for auth integration.

## Omitted: ML Anomaly Detection

Validation is deterministic and explainable. ML anomaly detection would be harder to defend without training data and would distract from auditability.
