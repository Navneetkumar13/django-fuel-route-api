import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from maprouter.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel stations from the fuel price CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/fuel-prices-for-be-assessment.csv",
            help="Path to the fuel price CSV file",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing fuel stations before importing",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file"])

        if not csv_path.exists():
            raise CommandError(
                f"CSV file not found: {csv_path}"
            )

        if options["clear"]:
            deleted_count, _ = FuelStation.objects.all().delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_count} existing records."
                )
            )

        self.stdout.write(
            f"Reading CSV file: {csv_path}"
        )

        stations = []

        with csv_path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:

            reader = csv.DictReader(csv_file)

            required_columns = {
                "OPIS Truckstop ID",
                "Truckstop Name",
                "Address",
                "City",
                "State",
                "Rack ID",
                "Retail Price",
            }

            actual_columns = set(reader.fieldnames or [])
            missing_columns = required_columns - actual_columns

            if missing_columns:
                raise CommandError("CSV is missing columns: " + ", ".join(sorted(missing_columns)))

            for row_number, row in enumerate(reader, start=2):
                try:
                    truckstop_id = int(row["OPIS Truckstop ID"])
                    rack_id = int(row["Rack ID"])
                    retail_price = float(row["Retail Price"])
                    station = FuelStation(
                        truckstop_id=truckstop_id,
                        name=row["Truckstop Name"].strip(),
                        address=row["Address"].strip(),
                        city=row["City"].strip(),
                        state=row["State"].strip().upper(),
                        rack_id=rack_id,
                        retail_price=retail_price,
                        latitude=None,
                        longitude=None
                    )

                    stations.append(station)

                except (ValueError, TypeError) as exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping row {row_number}: {exc}"
                        )
                    )

        self.stdout.write(f"Prepared {len(stations)} fuel stations.")

        with transaction.atomic():
            FuelStation.objects.bulk_create(
                stations,
                batch_size=1000,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(stations)} fuel stations."
            )
        )