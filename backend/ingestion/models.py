from django.conf import settings
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SourceType(models.TextChoices):
    SAP_FUEL = "SAP_FUEL", "SAP fuel/procurement"
    UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility electricity"
    CORPORATE_TRAVEL = "CORPORATE_TRAVEL", "Corporate travel"


class ProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"


class ReviewStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"


class IssueSeverity(models.TextChoices):
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"


class Company(TimestampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataSource(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="data_sources")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    name = models.CharField(max_length=255)
    external_system = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("company", "source_type", "name")]
        ordering = ["company__name", "source_type", "name"]

    def __str__(self):
        return f"{self.company}: {self.name}"


class RawUpload(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="raw_uploads")
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="uploads")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    records_total = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    records_needing_review = models.PositiveIntegerField(default=0)
    records_approved = models.PositiveIntegerField(default=0)
    failure_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]


class RawRecord(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="raw_records")
    raw_upload = models.ForeignKey(RawUpload, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    source_reference = models.CharField(max_length=255)
    original_payload = models.JSONField()
    parsing_status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING
    )
    parse_error = models.TextField(blank=True)

    class Meta:
        unique_together = [("raw_upload", "row_number")]
        ordering = ["raw_upload_id", "row_number"]


class SapGoodsMovementStaging(TimestampedModel):
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name="sap_staging")
    plant_code = models.CharField(max_length=40, blank=True)
    posting_date = models.CharField(max_length=40, blank=True)
    quantity = models.CharField(max_length=40, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    material_description = models.CharField(max_length=255, blank=True)
    source_document = models.CharField(max_length=255, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)


class UtilityIntervalStaging(TimestampedModel):
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name="utility_staging")
    meter_id = models.CharField(max_length=80, blank=True)
    period_start = models.CharField(max_length=40, blank=True)
    period_end = models.CharField(max_length=40, blank=True)
    usage = models.CharField(max_length=40, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    source_document = models.CharField(max_length=255, blank=True)
    tariff_description = models.CharField(max_length=255, blank=True)


class TravelExpenseStaging(TimestampedModel):
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name="travel_staging")
    expense_id = models.CharField(max_length=80, blank=True)
    expense_type = models.CharField(max_length=80, blank=True)
    transaction_date = models.CharField(max_length=40, blank=True)
    amount = models.CharField(max_length=40, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)
    origin_airport = models.CharField(max_length=10, blank=True)
    destination_airport = models.CharField(max_length=10, blank=True)
    distance_km = models.CharField(max_length=40, blank=True)
    hotel_nights = models.CharField(max_length=40, blank=True)


class NormalizedRecord(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="normalized_records")
    raw_record = models.OneToOneField(RawRecord, on_delete=models.PROTECT, related_name="normalized_record")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    activity_category = models.CharField(max_length=80)
    scope_category = models.CharField(max_length=20)
    original_unit = models.CharField(max_length=40, blank=True)
    normalized_unit = models.CharField(max_length=40)
    original_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    source_record_reference = models.CharField(max_length=255)
    facility_or_entity = models.CharField(max_length=120, blank=True)
    supplier_or_vendor = models.CharField(max_length=120, blank=True)
    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    locked_for_audit = models.BooleanField(default=False)
    normalized_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "source_type", "review_status"]),
            models.Index(fields=["company", "locked_for_audit"]),
            models.Index(fields=["activity_date"]),
        ]
        ordering = ["-created_at"]


class ValidationIssue(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="validation_issues")
    raw_record = models.ForeignKey(RawRecord, on_delete=models.CASCADE, related_name="validation_issues")
    normalized_record = models.ForeignKey(
        NormalizedRecord, null=True, blank=True, on_delete=models.CASCADE, related_name="validation_issues"
    )
    severity = models.CharField(max_length=20, choices=IssueSeverity.choices)
    code = models.CharField(max_length=80)
    message = models.TextField()
    field = models.CharField(max_length=80, blank=True)

    class Meta:
        indexes = [models.Index(fields=["company", "severity", "code"])]
        ordering = ["-created_at"]


class AnalystReview(TimestampedModel):
    normalized_record = models.ForeignKey(
        NormalizedRecord, on_delete=models.CASCADE, related_name="analyst_reviews"
    )
    previous_status = models.CharField(max_length=20, choices=ReviewStatus.choices)
    new_status = models.CharField(max_length=20, choices=ReviewStatus.choices)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    reviewed_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-reviewed_at"]


class AuditLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditLog entries are append-only")
        return super().save(*args, **kwargs)
