# Architectural & Product Decisions

This document captures the rationale behind the key technical and product decisions made during the development of the prototype.

## Ingestion Format: CSV vs. IDoc (SAP)
**Decision**: SAP fuel and procurement data is ingested via CSV extracts rather than native IDoc files.
**Rationale**: CSV data was used for ingestion because publicly accessible and complete IDoc datasets were not readily available. While IDoc files provide a more realistic SAP enterprise integration format, they typically require SAP-specific middleware, integration utilities, and system access for proper processing and transformation. For the scope of this assignment, CSV data provided a simpler and more practical approach while still allowing accurate ingestion, analysis, and visualization of ESG-related information.

## Technology Stack: Django + React
**Decision**: Use Django (Python) for the backend and React (TypeScript) for the frontend.
**Rationale**: 
- **Django**: Provides "batteries-included" support for multi-tenancy, audit logging, and complex data modeling via its ORM. The ecosystem for data processing in Python is unparalleled.
- **React**: Allows for a highly interactive "Review & Approval" dashboard. TypeScript ensures type safety across the API boundary.

## Visibility of "Suspicious" Data
**Decision**: Surface `WARNING` severity issues alongside `ERROR` issues in the analyst dashboard.
**Rationale**: In ESG reporting, data that is "suspicious" (e.g., a utility bill that is 10x higher than the previous month) is often more dangerous than data that is clearly wrong. By surfacing these as "Suspicious" in the UI, we empower the analyst to investigate the root cause before the data is locked for audit.

## Multi-Tenancy at the Row Level
**Decision**: Implement tenant isolation via a `Company` foreign key on all tables.
**Rationale**: While schema-per-tenant is an option, row-level isolation is more flexible for a prototype and allows for easier cross-tenant analytics (if authorized) and simpler infrastructure management on platforms like Heroku or Render.

## Synchronous Processing Pipeline
**Decision**: Process uploads synchronously in the current request.
**Rationale**: For the sample datasets provided, synchronous processing is instantaneous. For production scale (millions of rows), this would be moved to an asynchronous Celery/Redis worker queue. Keeping it synchronous for the prototype reduces infrastructure complexity for the reviewer.

---

## PM Questions for Production Readiness

1.  **Unlock Authority**: Who should have the authority to "Unlock" a record that has been locked for audit? Should this require a multi-person approval workflow?
2.  **Custom Mapping Tables**: Should we provide a UI for analysts to manage their own unit conversion factors and plant-code-to-facility mappings?
3.  **Source Reliability**: How do we handle "Estimated" vs. "Actual" reads in Utility data? Should "Estimated" reads be flagged as a permanent warning?
4.  **Data Deletion**: What is the data retention policy? If a tenant leaves, how do we handle the "Append-only" audit logs?
5.  **Emissions Logic**: Is the calculation of CO2e expected to happen inside this platform, or should we expose an API for a 3rd-party emissions engine?
