from decimal import Decimal

from .normalization import KNOWN_FUELS, VALID_AIRPORTS


def issue(severity, code, message, field=""):
    return {"severity": severity, "code": code, "message": message, "field": field}


def validate_sap(payload, normalized):
    issues = []
    fuel = str(payload.get("fuel_type") or "").strip().lower()
    if not normalized.get("original_unit"):
        issues.append(issue("ERROR", "MISSING_UNIT", "Fuel unit is missing", "unit"))
    if fuel and fuel not in KNOWN_FUELS:
        issues.append(issue("WARNING", "UNKNOWN_FUEL_TYPE", f"Unknown fuel type: {fuel}", "fuel_type"))
    if normalized.get("original_value") is None:
        issues.append(issue("ERROR", "INVALID_VALUE", "Fuel quantity could not be parsed", "quantity"))
    elif normalized["original_value"] < 0:
        issues.append(issue("ERROR", "NEGATIVE_USAGE", "Fuel quantity is negative", "quantity"))
    elif normalized["normalized_value"] and normalized["normalized_value"] > Decimal("50000"):
        issues.append(issue("WARNING", "SUSPICIOUSLY_LARGE_VALUE", "Fuel quantity is unusually large", "quantity"))
    if not normalized.get("activity_date"):
        issues.append(issue("ERROR", "MALFORMED_DATE", "Posting date could not be parsed", "posting_date"))
    return issues


def validate_utility(payload, normalized):
    issues = []
    if not normalized.get("original_unit"):
        issues.append(issue("ERROR", "MISSING_UNIT", "Electricity unit is missing", "unit"))
    if normalized.get("original_value") is None:
        issues.append(issue("ERROR", "INVALID_VALUE", "Usage value could not be parsed", "usage"))
    elif normalized["original_value"] < 0:
        issues.append(issue("ERROR", "NEGATIVE_USAGE", "Electricity usage is negative", "usage"))
    elif normalized["normalized_value"] and normalized["normalized_value"] > Decimal("250000"):
        issues.append(issue("WARNING", "SUSPICIOUSLY_LARGE_VALUE", "Meter usage is unusually large", "usage"))
    if not normalized.get("period_start") or not normalized.get("period_end"):
        issues.append(issue("ERROR", "MALFORMED_DATE", "Billing period dates could not be parsed", "billing_period"))
    elif normalized["period_end"] < normalized["period_start"]:
        issues.append(issue("ERROR", "INVALID_PERIOD", "Billing period ends before it starts", "billing_period"))
    return issues


def validate_travel(payload, normalized):
    issues = []
    category = normalized.get("activity_category")
    if normalized.get("original_value") is not None and normalized["original_value"] < 0:
        issues.append(issue("ERROR", "NEGATIVE_USAGE", "Travel activity value is negative", "value"))
    if category == "flight":
        origin = str(payload.get("origin_airport") or "").upper()
        dest = str(payload.get("destination_airport") or "").upper()
        if origin not in VALID_AIRPORTS:
            issues.append(issue("ERROR", "INVALID_AIRPORT_CODE", f"Invalid origin airport: {origin}", "origin_airport"))
        if dest not in VALID_AIRPORTS:
            issues.append(issue("ERROR", "INVALID_AIRPORT_CODE", f"Invalid destination airport: {dest}", "destination_airport"))
        if normalized.get("original_value") is None:
            issues.append(issue("WARNING", "MISSING_DISTANCE", "Flight distance missing; route lookup required", "distance_km"))
    elif category == "hotel" and normalized.get("original_value") is None:
        issues.append(issue("ERROR", "INVALID_VALUE", "Hotel nights could not be parsed", "nights"))
    elif category == "ground_transport" and normalized.get("original_value") is None:
        issues.append(issue("ERROR", "INVALID_VALUE", "Ground transport distance or amount could not be parsed", "distance_km"))
    if not normalized.get("activity_date"):
        issues.append(issue("ERROR", "MALFORMED_DATE", "Travel activity date could not be parsed", "date"))
    return issues
