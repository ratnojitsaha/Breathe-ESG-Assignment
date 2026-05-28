from django.db import transaction
from ingestion.models import (
    NormalizedRecord,
    ProcessingStatus,
    ReviewStatus,
    ValidationIssue,
    TravelExpenseStaging,
)

@transaction.atomic
def normalize_travel_row(raw_record, payload, normalized_data, validator):
    # Staging Layer
    staging = TravelExpenseStaging.objects.create(
        raw_record=raw_record,
        expense_id=str(payload.get("expense_id", "")),
        expense_type=str(payload.get("expense_type", "")),
        transaction_date=str(payload.get("transaction_date", "")),
        amount=str(payload.get("amount", "")),
        currency=str(payload.get("currency", "")),
        vendor_name=str(payload.get("vendor_name", "")),
        origin_airport=str(payload.get("origin_airport", "")),
        destination_airport=str(payload.get("destination_airport", "")),
        distance_km=str(payload.get("distance_km", "")),
        hotel_nights=str(payload.get("hotel_nights", "")),
    )

    # Activity Layer
    normalized = NormalizedRecord.objects.create(
        company=raw_record.company,
        raw_record=raw_record,
        source_type=raw_record.raw_upload.source_type,
        **normalized_data,
    )

    # Validation
    issues = validator(payload, normalized_data)
    has_error = any(item["severity"] == "ERROR" for item in issues)
    
    if issues:
        normalized.review_status = ReviewStatus.NEEDS_REVIEW
        normalized.save(update_fields=["review_status", "updated_at"])
    
    for item in issues:
        ValidationIssue.objects.create(
            company=raw_record.company,
            raw_record=raw_record,
            normalized_record=normalized,
            **item,
        )

    if has_error:
        raw_record.parsing_status = ProcessingStatus.FAILED
        raw_record.parse_error = "Validation error; analyst review required"
        raw_record.save(update_fields=["parsing_status", "parse_error", "updated_at"])
        return False, True # approved, failed

    return True, False # approved, failed
