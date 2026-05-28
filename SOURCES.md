# Source Data Research & Assumptions

This document details the research into the real-world formats for SAP, Utility, and Travel data that informed the design of our parsers and sample datasets.

## 1. SAP Fuel & Procurement (Scope 1)
**Real-World Context**: SAP ECC and S/4HANA systems typically manage fuel procurement through Goods Movement (MM) or Procurement (PO) modules.
- **Research**: We looked at common IDoc structures (like `MBGMCR03`) and standard ALV grid exports. These formats often include plant codes (`Werk`), posting dates (`Buchungsdatum`), and material types.
- **Sample Realism**: `samples/sap_fuel_export.csv` includes:
    - Inconsistent header casing and German labels (e.g., `Menge` for Quantity).
    - Messy date formats (e.g., `20260315` and `15.03.2026`).
    - Negative quantities representing reversals or returns.
- **Production Risks**: In a real deployment, custom movement types (Z-codes) and plant-specific unit-of-measure overrides would require a robust mapping table managed by the admin.

## 2. Utility Electricity (Scope 2)
**Real-World Context**: Commercial utility data is often retrieved from portal exports or "Green Button" standard files.
- **Research**: Commercial bills rarely align with calendar months. They often feature multiple meters per building and usage intervals (15/30/60 min).
- **Sample Realism**: `samples/utility_electricity_export.csv` includes:
    - Billing periods that cross month boundaries (e.g., Feb 15 to March 14).
    - Unit mix (kWh and MWh).
    - A "Suspiciously" high usage row designed to trigger a dashboard warning.
- **Production Risks**: "Estimated" reads are common in utility data. A production system would need to flag whether a record is based on an actual meter reading or a provider's estimate.

## 3. Corporate Travel (Scope 3)
**Real-World Context**: Systems like SAP Concur, Navan, or Egencia expose data via JSON APIs or scheduled flat-file exports.
- **Research**: Travel data is hierarchical. A single "Expense" might contain multiple "Itinerary Segments" (Flights, Hotels, Rail).
- **Sample Realism**: `samples/corporate_travel_concur.json` includes:
    - IATA airport codes (e.g., `JFK`, `LHR`).
    - Mixed categories: Flights (Distance-based) and Hotels (Night-based).
    - Validation triggers: An invalid airport code (`XYZ`) and a missing distance for a flight.
- **Production Risks**: Distance calculation (Great Circle Distance vs. Actual Flown) is a common source of discrepancy. A production system would integrate with a distance API (like the ICAO API) for validation.

---

## Why CSV for this Prototype?
While IDoc (SAP) and Green Button XML (Utility) are more "native" enterprise formats, **CSV was chosen for this prototype** to demonstrate high-fidelity ingestion, analysis, and visualization without requiring the proprietary middleware and system access usually needed to process those complex binary/XML structures. The logic within our parsers, however, is designed to be easily extended to these native formats.
