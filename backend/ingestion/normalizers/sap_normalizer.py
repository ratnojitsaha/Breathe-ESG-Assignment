from django.db import transaction
from ingestion.models import (
    NormalizedRecord,
    ProcessingStatus,
    ReviewStatus,
    ValidationIssue,
    SapGoodsMovementStaging,
)

@transaction.atomic
def normalize_sap_row(raw_record, payload, normalized_data, validator):
    # Staging Layer: Store specific fields
    staging = SapGoodsMovementStaging.objects.create(
        raw_record=raw_record,
        plant_code=str(payload.get("plant_code", "")),
        posting_date=str(payload.get("posting_date", "")),
        quantity=str(payload.get("quantity", "")),
        unit=str(payload.get("unit", "")),
        material_description=str(payload.get("material_description", "")),
        source_document=str(payload.get("source_document", "")),
        vendor_name=str(payload.get("vendor_name", "")),
    )

    # Activity Layer: Create normalized record
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
