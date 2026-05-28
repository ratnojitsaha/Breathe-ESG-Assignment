# Generated for the ESG ingestion prototype.
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("entity_type", models.CharField(max_length=80)),
                ("entity_id", models.CharField(max_length=80)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="ingestion.company")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DataSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_type", models.CharField(choices=[("SAP_FUEL", "SAP fuel/procurement"), ("UTILITY_ELECTRICITY", "Utility electricity"), ("CORPORATE_TRAVEL", "Corporate travel")], max_length=32)),
                ("name", models.CharField(max_length=255)),
                ("external_system", models.CharField(blank=True, max_length=255)),
                ("active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="data_sources", to="ingestion.company")),
            ],
            options={"ordering": ["company__name", "source_type", "name"], "unique_together": {("company", "source_type", "name")}},
        ),
        migrations.CreateModel(
            name="RawUpload",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_type", models.CharField(choices=[("SAP_FUEL", "SAP fuel/procurement"), ("UTILITY_ELECTRICITY", "Utility electricity"), ("CORPORATE_TRAVEL", "Corporate travel")], max_length=32)),
                ("original_filename", models.CharField(max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=120)),
                ("uploaded_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSED", "Processed"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("records_total", models.PositiveIntegerField(default=0)),
                ("records_failed", models.PositiveIntegerField(default=0)),
                ("records_needing_review", models.PositiveIntegerField(default=0)),
                ("records_approved", models.PositiveIntegerField(default=0)),
                ("failure_message", models.TextField(blank=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_uploads", to="ingestion.company")),
                ("data_source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploads", to="ingestion.datasource")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="RawRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("row_number", models.PositiveIntegerField()),
                ("source_reference", models.CharField(max_length=255)),
                ("original_payload", models.JSONField()),
                ("parsing_status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSED", "Processed"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("parse_error", models.TextField(blank=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.company")),
                ("raw_upload", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.rawupload")),
            ],
            options={"ordering": ["raw_upload_id", "row_number"], "unique_together": {("raw_upload", "row_number")}},
        ),
        migrations.CreateModel(
            name="NormalizedRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_type", models.CharField(choices=[("SAP_FUEL", "SAP fuel/procurement"), ("UTILITY_ELECTRICITY", "Utility electricity"), ("CORPORATE_TRAVEL", "Corporate travel")], max_length=32)),
                ("activity_category", models.CharField(max_length=80)),
                ("scope_category", models.CharField(max_length=20)),
                ("original_unit", models.CharField(blank=True, max_length=40)),
                ("normalized_unit", models.CharField(max_length=40)),
                ("original_value", models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True)),
                ("normalized_value", models.DecimalField(blank=True, decimal_places=4, max_digits=18, null=True)),
                ("activity_date", models.DateField(blank=True, null=True)),
                ("period_start", models.DateField(blank=True, null=True)),
                ("period_end", models.DateField(blank=True, null=True)),
                ("source_record_reference", models.CharField(max_length=255)),
                ("facility_or_entity", models.CharField(blank=True, max_length=120)),
                ("supplier_or_vendor", models.CharField(blank=True, max_length=120)),
                ("review_status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("NEEDS_REVIEW", "Needs review")], default="PENDING", max_length=20)),
                ("locked_for_audit", models.BooleanField(default=False)),
                ("normalized_payload", models.JSONField(blank=True, default=dict)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="normalized_records", to="ingestion.company")),
                ("raw_record", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="normalized_record", to="ingestion.rawrecord")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AnalystReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("previous_status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("NEEDS_REVIEW", "Needs review")], max_length=20)),
                ("new_status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("NEEDS_REVIEW", "Needs review")], max_length=20)),
                ("reviewed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("comment", models.TextField(blank=True)),
                ("normalized_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analyst_reviews", to="ingestion.normalizedrecord")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-reviewed_at"]},
        ),
        migrations.CreateModel(
            name="ValidationIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("severity", models.CharField(choices=[("WARNING", "Warning"), ("ERROR", "Error")], max_length=20)),
                ("code", models.CharField(max_length=80)),
                ("message", models.TextField()),
                ("field", models.CharField(blank=True, max_length=80)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="validation_issues", to="ingestion.company")),
                ("normalized_record", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="validation_issues", to="ingestion.normalizedrecord")),
                ("raw_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="validation_issues", to="ingestion.rawrecord")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="normalizedrecord", index=models.Index(fields=["company", "source_type", "review_status"], name="ingestion_n_company_841d3d_idx")),
        migrations.AddIndex(model_name="normalizedrecord", index=models.Index(fields=["company", "locked_for_audit"], name="ingestion_n_company_bbf558_idx")),
        migrations.AddIndex(model_name="normalizedrecord", index=models.Index(fields=["activity_date"], name="ingestion_n_activit_0adaeb_idx")),
        migrations.AddIndex(model_name="validationissue", index=models.Index(fields=["company", "severity", "code"], name="ingestion_v_company_dfa938_idx")),
    ]
