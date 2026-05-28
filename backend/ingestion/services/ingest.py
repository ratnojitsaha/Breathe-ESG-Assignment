from ingestion.models import (
    AuditLog,
    ProcessingStatus,
    RawRecord,
    RawUpload,
    SourceType,
)

from .parsers import parse_sap_rows, parse_travel_rows, parse_utility_rows
from .validation import validate_sap, validate_travel, validate_utility
from ingestion.normalizers.sap_normalizer import normalize_sap_row
from ingestion.normalizers.utility_normalizer import normalize_utility_row
from ingestion.normalizers.travel_normalizer import normalize_travel_row


PARSER_MAP = {
    SourceType.SAP_FUEL: (parse_sap_rows, validate_sap, normalize_sap_row),
    SourceType.UTILITY_ELECTRICITY: (parse_utility_rows, validate_utility, normalize_utility_row),
    SourceType.CORPORATE_TRAVEL: (parse_travel_rows, validate_travel, normalize_travel_row),
}


def ingest_upload(raw_upload: RawUpload, file_obj, actor=None):
    parser, validator, normalizer = PARSER_MAP[raw_upload.source_type]
    totals = {"total": 0, "failed": 0, "review": 0, "approved": 0}

    try:
        # We no longer wrap the whole thing in atomic. Each row is atomic in the normalizer.
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
            
            # Delegate to source-specific normalizer (which handles staging, activity layer, and validation)
            is_approved, is_failed = normalizer(raw_record, payload, normalized_data, validator)
            
            if is_failed:
                totals["failed"] += 1
            if is_approved:
                totals["approved"] += 1
            else:
                totals["review"] += 1

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
