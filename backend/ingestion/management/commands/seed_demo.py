from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from ingestion.models import Company, DataSource, RawUpload, SourceType
from ingestion.services.ingest import ingest_upload


class Command(BaseCommand):
    help = "Seed a demo tenant and data sources."

    def handle(self, *args, **options):
        companies = [
            ("acme-manufacturing", "Acme Manufacturing GmbH"),
            ("rhein-industries", "Rhein Industries AG"),
        ]
        source_specs = [
            (SourceType.SAP_FUEL, "SAP S/4HANA MM export", "SAP S/4HANA", "sap_fuel_export.csv", "text/csv"),
            (
                SourceType.UTILITY_ELECTRICITY,
                "Stadtwerke portal CSV",
                "Utility portal",
                "utility_electricity_export.csv",
                "text/csv",
            ),
            (
                SourceType.CORPORATE_TRAVEL,
                "Concur expense export",
                "Concur-like JSON",
                "corporate_travel_concur.json",
                "application/json",
            ),
        ]
        samples_dir = settings.BASE_DIR.parent / "samples"

        for slug, name in companies:
            company, _ = Company.objects.get_or_create(slug=slug, defaults={"name": name})
            for source_type, source_name, external, filename, content_type in source_specs:
                data_source, _ = DataSource.objects.get_or_create(
                    company=company,
                    source_type=source_type,
                    name=source_name,
                    defaults={"external_system": external},
                )
                if RawUpload.objects.filter(company=company, data_source=data_source).exists():
                    continue
                sample_path = samples_dir / filename
                if not Path(sample_path).exists():
                    self.stdout.write(self.style.WARNING(f"Sample file missing: {sample_path}"))
                    continue
                upload = RawUpload.objects.create(
                    company=company,
                    data_source=data_source,
                    source_type=source_type,
                    original_filename=filename,
                    content_type=content_type,
                )
                file_obj = SimpleUploadedFile(filename, sample_path.read_bytes(), content_type=content_type)
                ingest_upload(upload, file_obj)

        self.stdout.write(self.style.SUCCESS("Seeded demo companies, data sources, and sample ingestions."))
