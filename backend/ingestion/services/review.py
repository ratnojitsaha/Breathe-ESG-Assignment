from django.db import transaction
from django.utils import timezone

from ingestion.models import AnalystReview, AuditLog, NormalizedRecord, ReviewStatus


@transaction.atomic
def review_record(record: NormalizedRecord, new_status, actor=None, comment=""):
    if record.locked_for_audit:
        raise ValueError("Audit-locked records cannot be changed")
    if new_status not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        raise ValueError("Review status must be APPROVED or REJECTED")

    before = {
        "review_status": record.review_status,
        "locked_for_audit": record.locked_for_audit,
    }
    previous = record.review_status
    record.review_status = new_status
    record.locked_for_audit = new_status == ReviewStatus.APPROVED
    record.save(update_fields=["review_status", "locked_for_audit", "updated_at"])

    AnalystReview.objects.create(
        normalized_record=record,
        previous_status=previous,
        new_status=new_status,
        reviewed_by=actor,
        reviewed_at=timezone.now(),
        comment=comment,
    )
    after = {
        "review_status": record.review_status,
        "locked_for_audit": record.locked_for_audit,
    }
    AuditLog.objects.create(
        company=record.company,
        actor=actor,
        action="NORMALIZED_RECORD_REVIEWED",
        entity_type="NormalizedRecord",
        entity_id=str(record.id),
        before=before,
        after=after,
        metadata={"comment": comment},
    )
    return record
