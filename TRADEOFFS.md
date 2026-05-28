# Engineering Tradeoffs

This document outlines the features and architectural patterns that were deliberately omitted to focus on the core deliverables of data lineage and analyst workflow.

## 1. Omitted: Automated Emissions Factor Matching
**Why?**: Matching activity data (e.g., "500L Diesel") to an emissions factor (e.g., "DEFRA 2023 Diesel Fuel") is a massive undertaking involving geography, timing, and methodology versioning.
**Tradeoff**: We focused on **Normalization** and **Validation**. By ensuring the activity data is clean, normalized, and audit-ready, we provide a solid foundation for any 3rd-party emissions engine to perform the final CO2e calculations.

## 2. Omitted: PDF/OCR Ingestion for Utility Bills
**Why?**: While utility data often arrives as PDFs, building a robust OCR pipeline is a distraction from the core goal of demonstrating data modeling and multi-tenancy.
**Tradeoff**: We chose **CSV Ingestion** for utility data. This allowed us to focus on handling complex non-calendar billing cycles and meter-level tracking, which are the primary data modeling challenges in Scope 2 reporting.

## 3. Omitted: Distributed Task Queue (Celery/Redis)
**Why?**: In a production enterprise environment, ingestion should be asynchronous to prevent request timeouts and allow for retries.
**Tradeoff**: We implemented **Synchronous Processing**. This keeps the prototype's infrastructure simple (no need for a Redis broker) and allows the reviewer to see immediate results in the UI without waiting for background workers. The code is structured such that parsers can be easily wrapped in Celery tasks in the future.

---

## Future Roadmap (Next Steps)
If this were to move beyond a prototype, the following would be prioritized:
- **SSO/OIDC Integration**: Support for enterprise authentication.
- **Advanced Anomaly Detection**: Moving beyond deterministic rules to ML-based detection for "Suspicious" data.
- **Supplier Portal**: Allowing vendors to upload their own Scope 3 data directly into the platform for review.
