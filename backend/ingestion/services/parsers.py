import csv
import io
import json

from .normalization import decimal_or_none, midpoint, normalize_unit, parse_date


TRAVEL_CATEGORY_ALIASES = {
    "flight": "flight",
    "air": "flight",
    "plane": "flight",
    "hotel": "hotel",
    "lodging": "hotel",
    "ground_transport": "ground_transport",
    "ground transport": "ground_transport",
    "taxi": "ground_transport",
    "cab": "ground_transport",
    "ride": "ground_transport",
    "ride_hailing": "ground_transport",
    "car_rental": "ground_transport",
    "car rental": "ground_transport",
    "train": "ground_transport",
    "rail": "ground_transport",
    "bus": "ground_transport",
}


SAP_HEADER_MAP = {
    "plant": "plant_code",
    "werk": "plant_code",
    "werks": "plant_code",
    "posting date": "posting_date",
    "buchungsdatum": "posting_date",
    "erdat": "posting_date",
    "abdat": "posting_date",
    "material": "fuel_type",
    "fuel type": "fuel_type",
    "arktx": "fuel_type",
    "matnr": "material_code",
    "menge": "quantity",
    "quantity": "quantity",
    "zmeng": "quantity",
    "unit": "unit",
    "meins": "unit",
    "vendor": "vendor",
    "lieferant": "vendor",
    "lifnr": "vendor",
    "po number": "source_document",
    "eban": "source_document",
    "vbeln": "source_document",
}

UTILITY_HEADER_MAP = {
    "meter id": "meter_id",
    "meter": "meter_id",
    "service address": "service_address",
    "period start": "period_start",
    "period end": "period_end",
    "usage": "usage",
    "usage kwh": "usage",
    "unit": "unit",
    "tariff": "tariff",
    "rate plan": "tariff",
    "bill number": "source_document",
}


def parse_csv_upload(file_obj, header_map):
    text = file_obj.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    for index, row in enumerate(reader, start=2):
        yield index, normalize_headers(row, header_map)


def normalize_headers(row, header_map):
    normalized = {}
    for key, value in row.items():
        mapped = header_map.get((key or "").strip().lower(), (key or "").strip().lower().replace(" ", "_"))
        normalized[mapped] = value.strip() if isinstance(value, str) else value
    return normalized


def parse_sap_rows(file_obj):
    for row_number, payload in parse_csv_upload(file_obj, SAP_HEADER_MAP):
        value = decimal_or_none(payload.get("quantity"))
        normalized_value, normalized_unit = normalize_unit(value, payload.get("unit"), "fuel")
        yield row_number, payload, {
            "activity_category": "fuel_combustion",
            "scope_category": "Scope 1",
            "original_unit": payload.get("unit") or "",
            "normalized_unit": normalized_unit,
            "original_value": value,
            "normalized_value": normalized_value,
            "activity_date": parse_date(payload.get("posting_date")),
            "period_start": None,
            "period_end": None,
            "facility_or_entity": payload.get("plant_code") or "",
            "supplier_or_vendor": payload.get("vendor") or "",
            "source_record_reference": payload.get("source_document") or f"SAP-row-{row_number}",
            "normalized_payload": {
                "fuel_type": payload.get("fuel_type"),
                "material_code": payload.get("material_code"),
                "plant_code": payload.get("plant_code"),
            },
        }


def parse_utility_rows(file_obj):
    for row_number, payload in parse_csv_upload(file_obj, UTILITY_HEADER_MAP):
        value = decimal_or_none(payload.get("usage"))
        original_unit = payload.get("unit") or ""
        if original_unit:
            normalized_value, normalized_unit = normalize_unit(value, original_unit, "electricity")
        else:
            normalized_value, normalized_unit = None, ""
        period_start = parse_date(payload.get("period_start"))
        period_end = parse_date(payload.get("period_end"))
        yield row_number, payload, {
            "activity_category": "purchased_electricity",
            "scope_category": "Scope 2",
            "original_unit": original_unit,
            "normalized_unit": normalized_unit,
            "original_value": value,
            "normalized_value": normalized_value,
            "activity_date": midpoint(period_start, period_end),
            "period_start": period_start,
            "period_end": period_end,
            "facility_or_entity": payload.get("meter_id") or "",
            "supplier_or_vendor": payload.get("tariff") or "",
            "source_record_reference": payload.get("source_document") or f"UTILITY-row-{row_number}",
            "normalized_payload": {
                "meter_id": payload.get("meter_id"),
                "tariff": payload.get("tariff"),
                "service_address": payload.get("service_address"),
            },
        }


def parse_travel_rows(file_obj):
    data = json.loads(file_obj.read().decode("utf-8"))
    records = data if isinstance(data, list) else data.get("expenses", [])
    for index, payload in enumerate(records, start=1):
        raw_category = str(payload.get("type") or payload.get("category") or "").strip().lower()
        category = TRAVEL_CATEGORY_ALIASES.get(raw_category, raw_category or "ground_transport")
        row_number = index
        if category == "flight":
            value = decimal_or_none(payload.get("distance_km"))
            normalized_unit = "km"
        elif category == "hotel":
            value = decimal_or_none(payload.get("nights"))
            normalized_unit = "room_night"
        else:
            category = "ground_transport"
            distance = payload.get("distance_km")
            value = decimal_or_none(distance if distance not in (None, "") else payload.get("amount"))
            normalized_unit = "km" if distance not in (None, "") else "trip"
        yield row_number, payload, {
            "activity_category": category,
            "scope_category": "Scope 3",
            "original_unit": normalized_unit,
            "normalized_unit": normalized_unit,
            "original_value": value,
            "normalized_value": value,
            "activity_date": parse_date(payload.get("date")),
            "period_start": None,
            "period_end": None,
            "facility_or_entity": payload.get("employee_cost_center") or "",
            "supplier_or_vendor": payload.get("vendor") or payload.get("airline") or "",
            "source_record_reference": payload.get("expense_id") or f"TRAVEL-row-{row_number}",
            "normalized_payload": {**payload, "normalized_category": category, "raw_category": raw_category},
        }
