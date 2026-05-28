import csv
import json
from pathlib import Path

from rest_framework import serializers

from .models import (
    AuditLog,
    Company,
    DataSource,
    NormalizedRecord,
    RawRecord,
    RawUpload,
    ReviewStatus,
    SourceType,
    ValidationIssue,
)
from .services.parsers import SAP_HEADER_MAP, UTILITY_HEADER_MAP


SAP_CSV_REQUIRED_FIELDS = {"plant_code", "posting_date", "quantity", "unit", "source_document"}
UTILITY_CSV_REQUIRED_FIELDS = {"meter_id", "period_start", "period_end", "usage", "unit", "source_document"}


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "slug"]


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["id", "company", "source_type", "name", "external_system", "active"]


class RawUploadSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source="data_source.name", read_only=True)

    class Meta:
        model = RawUpload
        fields = [
            "id",
            "company",
            "data_source",
            "data_source_name",
            "source_type",
            "original_filename",
            "content_type",
            "uploaded_at",
            "status",
            "records_total",
            "records_failed",
            "records_needing_review",
            "records_approved",
            "failure_message",
        ]
        read_only_fields = fields


class UploadCreateSerializer(serializers.Serializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    data_source = serializers.PrimaryKeyRelatedField(queryset=DataSource.objects.all())
    file = serializers.FileField()

    def validate(self, attrs):
        data_source = attrs["data_source"]
        upload_file = attrs["file"]
        filename = Path(upload_file.name or "").name.lower()
        if data_source.company_id != attrs["company"].id:
            raise serializers.ValidationError("Data source does not belong to company")
        if data_source.source_type in {SourceType.SAP_FUEL, SourceType.UTILITY_ELECTRICITY}:
            self._validate_csv_upload(upload_file, data_source.source_type, filename)
        elif data_source.source_type == SourceType.CORPORATE_TRAVEL:
            self._validate_travel_upload(upload_file, filename)
        return attrs

    def _read_file_bytes(self, upload_file):
        raw_bytes = upload_file.read()
        if hasattr(upload_file, "seek"):
            upload_file.seek(0)
        return raw_bytes

    def _validate_csv_upload(self, upload_file, source_type, filename):
        content_type = (getattr(upload_file, "content_type", "") or "").lower()
        if not filename.endswith(".csv") and content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
            raise serializers.ValidationError("SAP and utility source uploads must be CSV files")

        try:
            sample = self._read_file_bytes(upload_file).decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError("CSV upload must be UTF-8 encoded") from exc

        reader = csv.DictReader(sample.splitlines())
        header_map = SAP_HEADER_MAP if source_type == SourceType.SAP_FUEL else UTILITY_HEADER_MAP
        normalized_fields = {
            header_map.get((field or "").strip().lower(), (field or "").strip().lower().replace(" ", "_"))
            for field in (reader.fieldnames or [])
        }
        required_fields = SAP_CSV_REQUIRED_FIELDS if source_type == SourceType.SAP_FUEL else UTILITY_CSV_REQUIRED_FIELDS
        missing = required_fields - normalized_fields
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise serializers.ValidationError(f"CSV upload is missing required columns: {missing_list}")

    def _validate_travel_upload(self, upload_file, filename):
        content_type = (getattr(upload_file, "content_type", "") or "").lower()
        if not filename.endswith(".json") and content_type != "application/json":
            raise serializers.ValidationError("Corporate travel source uploads must be JSON files")

        try:
            payload = json.loads(self._read_file_bytes(upload_file).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError("JSON upload must be UTF-8 encoded") from exc
        except json.JSONDecodeError as exc:
            raise serializers.ValidationError("Corporate travel upload must contain valid JSON") from exc

        records = payload if isinstance(payload, list) else payload.get("expenses") if isinstance(payload, dict) else None
        if not isinstance(records, list) or not records:
            raise serializers.ValidationError("Corporate travel JSON must include an expenses array")
        if not any(isinstance(item, dict) for item in records):
            raise serializers.ValidationError("Corporate travel JSON expenses must contain record objects")


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = [
            "id",
            "company",
            "raw_upload",
            "row_number",
            "source_reference",
            "original_payload",
            "parsing_status",
            "parse_error",
        ]


class ValidationIssueSerializer(serializers.ModelSerializer):
    raw_payload = serializers.JSONField(source="raw_record.original_payload", read_only=True)

    class Meta:
        model = ValidationIssue
        fields = [
            "id",
            "company",
            "raw_record",
            "normalized_record",
            "severity",
            "code",
            "message",
            "field",
            "raw_payload",
            "created_at",
        ]


class NormalizedRecordSerializer(serializers.ModelSerializer):
    issues = ValidationIssueSerializer(source="validation_issues", many=True, read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = [
            "id",
            "company",
            "raw_record",
            "source_type",
            "activity_category",
            "scope_category",
            "original_unit",
            "normalized_unit",
            "original_value",
            "normalized_value",
            "activity_date",
            "period_start",
            "period_end",
            "source_record_reference",
            "facility_or_entity",
            "supplier_or_vendor",
            "review_status",
            "locked_for_audit",
            "normalized_payload",
            "issues",
            "created_at",
        ]


class ReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[ReviewStatus.APPROVED, ReviewStatus.REJECTED])
    comment = serializers.CharField(required=False, allow_blank=True)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "company",
            "actor_email",
            "action",
            "entity_type",
            "entity_id",
            "before",
            "after",
            "metadata",
            "created_at",
        ]
