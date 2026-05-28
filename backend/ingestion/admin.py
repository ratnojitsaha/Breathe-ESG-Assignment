from django.contrib import admin

from .models import (
    AnalystReview,
    AuditLog,
    Company,
    DataSource,
    NormalizedRecord,
    RawRecord,
    RawUpload,
    ValidationIssue,
)


admin.site.register(Company)
admin.site.register(DataSource)
admin.site.register(RawUpload)
admin.site.register(RawRecord)
admin.site.register(NormalizedRecord)
admin.site.register(ValidationIssue)
admin.site.register(AnalystReview)
admin.site.register(AuditLog)
