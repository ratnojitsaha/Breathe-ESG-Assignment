from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    CompanyViewSet,
    DataSourceViewSet,
    NormalizedRecordViewSet,
    RawRecordViewSet,
    RawUploadViewSet,
    ValidationIssueViewSet,
)

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("data-sources", DataSourceViewSet, basename="data-source")
router.register("uploads", RawUploadViewSet, basename="upload")
router.register("raw-records", RawRecordViewSet, basename="raw-record")
router.register("normalized-records", NormalizedRecordViewSet, basename="normalized-record")
router.register("validation-issues", ValidationIssueViewSet, basename="validation-issue")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = router.urls
