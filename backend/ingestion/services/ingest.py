from django.db import transaction

from ingestion.models import (
    AuditLog,
    NormalizedRecord,
    ProcessingStatus,
    RawRecord,
    RawUpload,
    ReviewStatus,
    SourceType,
    ValidationIssue,
)

from .parsers import parse_sap_rows, parse_travel_rows, parse_utility_rows
from .validation import validate_sap, validate_travel, validate_utility


PARSER_BY_SOURCE = {
    SourceType.SAP_FUEL: (parse_sap_rows, validate_sap),
    SourceType.UTILITY_ELECTRICITY: (parse_utility_rows, validate_utility),
    SourceType.CORPORATE_TRAVEL: (parse_travel_rows, validate_travel),
}


def ingest_upload(raw_upload: RawUpload, file_obj, actor=None):
    parser, validator = PARSER_BY_SOURCE[raw_upload.source_type]
    totals = {"total": 0, "failed": 0, "review": 0, "approved": 0}

    try:
        with transaction.atomic():
            for row_number, payload, normalized_data in parser(file_obj):
                totals["total"] += 1
                raw_record = RawRecord.objects.create(
                    company=raw_upload.company,
                    raw_upload=raw_upload,
                    row_number=row_number,
                    source_reference=normalized_data["source_record_reference"],
                    original_payload=payload,
                    parsing_status=ProcessingStatus.PROCESSED,
                )
                normalized = NormalizedRecord.objects.create(
                    company=raw_upload.company,
                    raw_record=raw_record,
                    source_type=raw_upload.source_type,
                    **normalized_data,
                )
                issues = validator(payload, normalized_data)
                has_error = any(item["severity"] == "ERROR" for item in issues)
                if issues:
                    totals["review"] += 1
                    normalized.review_status = ReviewStatus.NEEDS_REVIEW
                    normalized.save(update_fields=["review_status", "updated_at"])
                else:
                    totals["approved"] += 1
                for item in issues:
                    ValidationIssue.objects.create(
                        company=raw_upload.company,
                        raw_record=raw_record,
                        normalized_record=normalized,
                        **item,
                    )
                if has_error:
                    raw_record.parsing_status = ProcessingStatus.FAILED
                    raw_record.parse_error = "Validation error; analyst review required"
                    raw_record.save(update_fields=["parsing_status", "parse_error", "updated_at"])
                    totals["failed"] += 1
    except Exception as exc:
        raw_upload.status = ProcessingStatus.FAILED
        raw_upload.failure_message = str(exc)
        raw_upload.save(update_fields=["status", "failure_message", "updated_at"])
        AuditLog.objects.create(
            company=raw_upload.company,
            actor=actor,
            action="UPLOAD_FAILED",
            entity_type="RawUpload",
            entity_id=str(raw_upload.id),
            after={"failure_message": str(exc)},
            metadata={"source_type": raw_upload.source_type, "filename": raw_upload.original_filename},
        )
        return raw_upload

    raw_upload.status = ProcessingStatus.PROCESSED
    raw_upload.records_total = totals["total"]
    raw_upload.records_failed = totals["failed"]
    raw_upload.records_needing_review = totals["review"]
    raw_upload.records_approved = totals["approved"]
    raw_upload.save(
        update_fields=[
            "status",
            "records_total",
            "records_failed",
            "records_needing_review",
            "records_approved",
            "updated_at",
        ]
    )
    AuditLog.objects.create(
        company=raw_upload.company,
        actor=actor,
        action="UPLOAD_INGESTED",
        entity_type="RawUpload",
        entity_id=str(raw_upload.id),
        after=totals,
        metadata={"source_type": raw_upload.source_type, "filename": raw_upload.original_filename},
    )
    return raw_upload
