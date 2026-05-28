from django.db.models import Count, Q, Sum
from rest_framework import mixins, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import (
    AuditLog,
    Company,
    DataSource,
    IssueSeverity,
    NormalizedRecord,
    RawRecord,
    RawUpload,
    ReviewStatus,
    ValidationIssue,
)
from .serializers import (
    AuditLogSerializer,
    CompanySerializer,
    DataSourceSerializer,
    NormalizedRecordSerializer,
    RawRecordSerializer,
    RawUploadSerializer,
    ReviewActionSerializer,
    UploadCreateSerializer,
    ValidationIssueSerializer,
)
from .services.ingest import ingest_upload
from .services.review import review_record


class PrototypeViewSetMixin:
    """Mixin to disable authentication and permissions for the prototype."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]


class CompanyViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        company = self.get_object()
        records = NormalizedRecord.objects.filter(company=company)
        issues = ValidationIssue.objects.filter(company=company)
        uploads = RawUpload.objects.filter(company=company)

        by_source = []
        for source_type, label in DataSource.objects.filter(company=company).values_list("source_type", "name"):
            source_records = records.filter(source_type=source_type)
            source_issues = issues.filter(raw_record__raw_upload__source_type=source_type)
            by_source.append(
                {
                    "source_type": source_type,
                    "name": label,
                    "records": source_records.count(),
                    "issues": source_issues.count(),
                    "errors": source_issues.filter(severity=IssueSeverity.ERROR).count(),
                    "warnings": source_issues.filter(severity=IssueSeverity.WARNING).count(),
                    "locked": source_records.filter(locked_for_audit=True).count(),
                }
            )

        return Response(
            {
                "company": CompanySerializer(company).data,
                "totals": {
                    "records": records.count(),
                    "needs_attention": records.filter(
                        review_status__in=[ReviewStatus.PENDING, ReviewStatus.NEEDS_REVIEW]
                    ).count(),
                    "failed_at_ingest": issues.filter(severity=IssueSeverity.ERROR).count(),
                    "awaiting_setup": issues.filter(
                        code__in=[
                            "MISSING_UNIT",
                            "UNKNOWN_FUEL_TYPE",
                            "INVALID_AIRPORT_CODE",
                            "MISSING_DISTANCE",
                        ]
                    ).count(),
                    "ready_to_lock": records.filter(review_status=ReviewStatus.APPROVED, locked_for_audit=False).count(),
                    "locked_for_audit": records.filter(locked_for_audit=True).count(),
                    "uploads": uploads.count(),
                },
                "by_source": by_source,
                "by_scope": list(
                    records.values("scope_category")
                    .annotate(records=Count("id"), activity_total=Sum("normalized_value"))
                    .order_by("scope_category")
                ),
                "recent_uploads": RawUploadSerializer(
                    uploads.select_related("data_source").order_by("-uploaded_at")[:5], many=True
                ).data,
            }
        )


class DataSourceViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DataSourceSerializer
    filterset_fields = ["company", "source_type", "active"]

    def get_queryset(self):
        return DataSource.objects.select_related("company").all()


class RawUploadViewSet(PrototypeViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = RawUploadSerializer
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["company", "source_type", "status"]

    def get_queryset(self):
        return RawUpload.objects.select_related("company", "data_source").all()

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        serializer = UploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data["file"]
        data_source = serializer.validated_data["data_source"]
        raw_upload = RawUpload.objects.create(
            company=serializer.validated_data["company"],
            data_source=data_source,
            source_type=data_source.source_type,
            original_filename=file_obj.name,
            content_type=getattr(file_obj, "content_type", ""),
            uploaded_by=request.user if request.user.is_authenticated else None,
        )
        ingest_upload(raw_upload, file_obj, request.user if request.user.is_authenticated else None)
        response_status = status.HTTP_400_BAD_REQUEST if raw_upload.status == "FAILED" else status.HTTP_201_CREATED
        return Response(RawUploadSerializer(raw_upload).data, status=response_status)


class RawRecordViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RawRecordSerializer
    filterset_fields = ["company", "raw_upload", "parsing_status"]

    def get_queryset(self):
        return RawRecord.objects.select_related("company", "raw_upload").all()


class NormalizedRecordViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = NormalizedRecordSerializer
    filterset_fields = ["company", "source_type", "review_status", "locked_for_audit", "scope_category"]

    def get_queryset(self):
        qs = NormalizedRecord.objects.select_related("company", "raw_record").prefetch_related("validation_issues")
        source_type = self.request.query_params.get("source_type")
        if source_type:
            qs = qs.filter(source_type=source_type)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(source_record_reference__icontains=search)
                | Q(activity_category__icontains=search)
                | Q(facility_or_entity__icontains=search)
            )
        return qs

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        record = self.get_object()
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review_record(
                record,
                serializer.validated_data["status"],
                request.user if request.user.is_authenticated else None,
                serializer.validated_data.get("comment", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(NormalizedRecordSerializer(record).data)


class ValidationIssueViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ValidationIssueSerializer
    filterset_fields = ["company", "severity", "code", "normalized_record", "raw_record"]

    def get_queryset(self):
        return ValidationIssue.objects.select_related("company", "raw_record", "normalized_record").all()


class AuditLogViewSet(PrototypeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    filterset_fields = ["company", "action", "entity_type", "entity_id"]

    def get_queryset(self):
        return AuditLog.objects.select_related("company", "actor").all()
