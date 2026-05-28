# Source Assumptions

## SAP Fuel / Procurement

Researched real-world shape: SAP ECC/S/4HANA material/procurement extracts often contain plant codes, posting dates, material descriptions, quantities, base units, vendors, and purchasing document references. German SAP configurations may use labels such as `Werk`, `Buchungsdatum`, `Menge`, `MEINS`, and `Lieferant`.

Sample realism: `samples/sap_fuel_export.csv` includes German-style dates, compact `YYYYMMDD`, inconsistent fuel units, plant codes, vendor names, purchasing references, a negative quantity, an unknown fuel type, and a malformed date.

Production risk: source-specific custom fields, plant lookup tables, unit-of-measure configuration, reversals, and duplicate purchasing documents would need deeper SAP integration.

## Utility Electricity

Researched real-world shape: utility portal exports commonly include meter IDs, service addresses, billing period start/end, usage, units, tariff/rate plan, and bill number. Billing periods often cross calendar months.

Sample realism: `samples/utility_electricity_export.csv` includes multiple meters, non-calendar billing cycles, kWh and MWh, industrial tariffs, a suspiciously large usage value, and a negative row.

Production risk: estimated reads, demand charges, time-of-use intervals, multiple registers, PDF-only providers, and regional utility formats would require provider-specific adapters.

## Corporate Travel

Researched real-world shape: travel and expense systems such as Concur/Navan expose expenses with category, date, employee/cost center, vendor, flight route, hotel nights, and ground transport fields. Flight distance may be missing while airport codes are present.

Sample realism: `samples/corporate_travel_concur.json` includes flights, hotel nights, taxis, cost centers, airline/vendor fields, real airport codes, one missing distance, and one invalid airport code.

Production risk: itinerary changes, multi-leg flights, train travel, refunds, cabin-class methodology, route distance lookup, and employee privacy handling would need stronger modeling.
