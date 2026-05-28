# Decisions

## Ambiguities Resolved

The assignment asks for realistic ingestion choices but allows each source mechanism to be chosen. I chose SAP and utility CSV uploads and travel JSON upload because they are common enough for onboarding workflows and small enough for a defensible prototype.

## Why CSV for SAP

SAP can expose IDocs, BAPIs, OData, and flat files. For onboarding, CSV exports from SAP ECC/S/4HANA are realistic because analysts and consultants often exchange extracts before formal integrations exist. The parser supports inconsistent headers, German labels, plant codes, messy dates, and inconsistent units.

## Why CSV for Utility

Facilities teams commonly download utility portal CSV exports. The model supports billing periods, meter IDs, tariffs, and non-calendar cycles. PDF bills and meter APIs were intentionally left out.

## Why JSON for Travel

Corporate travel platforms expose API-like expense objects. JSON better represents mixed travel categories than flattening flights, hotels, and taxis into one spreadsheet.

## Why Raw + Normalized Tables

Raw data is the evidence. Normalized data is the operational interpretation. Splitting them allows deterministic reprocessing, auditor comparison, and analyst review without losing source truth.

## Assumptions

- Scope 1: company fuel combustion.
- Scope 2: purchased electricity.
- Scope 3: business travel.
- Approved rows are immediately locked for audit.
- Emissions factor calculation is out of scope; this prototype normalizes activity data only.
- A single uploaded row maps to one normalized row.

## PM Questions For Production

- Should analysts be allowed to unlock approved records, and under whose authority?
- Are company-specific unit and plant-code mappings expected?
- Which source system ID should be treated as the legal source-of-truth reference?
- Should warnings block audit approval or only require comment capture?
- Are emissions factors part of this product surface or a downstream accounting service?
