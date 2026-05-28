from django.db import transaction
from ingestion.models import (
    NormalizedRecord,
    ProcessingStatus,
    ReviewStatus,
    ValidationIssue,
    UtilityIntervalStaging,
)

@transaction.atomic
def normalize_utility_row(raw_record, payload, normalized_data, validator):
    # Staging Layer
    staging = UtilityIntervalStaging.objects.create(
        raw_record=raw_record,
        meter_id=str(payload.get("meter_id", "")),
        period_start=str(payload.get("period_start", "")),
        period_end=str(payload.get("period_end", "")),
        usage=str(payload.get("usage", "")),
        unit=str(payload.get("unit", "")),
        source_document=str(payload.get("source_document", "")),
        tariff_description=str(payload.get("tariff_description", "")),
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
