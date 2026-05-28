from datetime import date, datetime
from decimal import Decimal, InvalidOperation


FUEL_UNITS_TO_LITERS = {
    "l": Decimal("1"),
    "liter": Decimal("1"),
    "litre": Decimal("1"),
    "liters": Decimal("1"),
    "ltr": Decimal("1"),
    "gal": Decimal("3.78541"),
    "gallon": Decimal("3.78541"),
    "kg": Decimal("1"),
}

ELECTRICITY_UNITS_TO_KWH = {
    "kwh": Decimal("1"),
    "kw h": Decimal("1"),
    "mwh": Decimal("1000"),
}

KNOWN_FUELS = {"diesel", "petrol", "gasoline", "natural gas", "lpg", "heating oil"}
VALID_AIRPORTS = {
    "AMS", "ATL", "BLR", "BOM", "CDG", "DEL", "DXB", "FRA", "JFK", "LAX",
    "LHR", "MAA", "MUC", "ORD", "SFO", "SIN", "ZRH",
}


def decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        return None


def parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_unit(value, unit, source_kind):
    if unit is None:
        return None, ""
    unit_key = str(unit).strip().lower()
    amount = decimal_or_none(value)
    if amount is None:
        return None, canonical_unit(source_kind)
    conversions = FUEL_UNITS_TO_LITERS if source_kind == "fuel" else ELECTRICITY_UNITS_TO_KWH
    factor = conversions.get(unit_key)
    if factor is None:
        return amount, canonical_unit(source_kind)
    return amount * factor, canonical_unit(source_kind)


def canonical_unit(source_kind):
    if source_kind == "fuel":
        return "L"
    if source_kind == "electricity":
        return "kWh"
    if source_kind == "distance":
        return "km"
    if source_kind == "hotel":
        return "room_night"
    return "unit"


def midpoint(start: date | None, end: date | None):
    if not start:
        return end
    if not end:
        return start
    return start + (end - start) / 2
