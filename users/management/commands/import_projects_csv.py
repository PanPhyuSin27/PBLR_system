import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from users.models import Project


SKILL_LEVEL_NORMALIZATION = {
    "beginner": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
}

PLAN_NORMALIZATION = {
    "explorer": "explorer",
    "free": "explorer",
    "pro_monthly": "pro_monthly",
    "pro monthly": "pro_monthly",
    "monthly": "pro_monthly",
    "pro_yearly": "pro_yearly",
    "pro yearly": "pro_yearly",
    "yearly": "pro_yearly",
    "annual": "pro_yearly",
}

REQUIRED_COLUMNS = [
    "title",
    "description",
    "field",
    "target_role",
    "skill_level",
    "required_plan",
    "tech_preference",
    "learning_goal",
    "interest_tags",
]

OPTIONAL_COLUMNS = [
    "learning_objectives",
    "resources",
    "task_checklist",
    "detailed_roadmap",
    "premium_hints",
]

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


class Command(BaseCommand):
    help = "Import projects from a CSV file (create new or update existing by title+field+target_role)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update rows that already exist (matched by title+field+target_role).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and preview import without writing to database.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]).expanduser().resolve()
        update_existing = options["update_existing"]
        dry_run = options["dry_run"]

        if not csv_path.exists() or not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise CommandError("CSV has no header row.")

            missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
            if missing:
                raise CommandError(f"Missing required columns: {', '.join(missing)}")

            for row_index, raw_row in enumerate(reader, start=2):
                row = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items()}

                try:
                    payload = self._build_payload(row, row_index)
                except CommandError as exc:
                    self.stderr.write(self.style.ERROR(str(exc)))
                    error_count += 1
                    continue

                lookup = {
                    "title": payload["title"],
                    "field": payload["field"],
                    "target_role": payload["target_role"],
                }
                existing = Project.objects.filter(**lookup).first()

                if existing:
                    if not update_existing:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Row {row_index}: skipped existing project '{payload['title']}' "
                                "(use --update-existing to update)."
                            )
                        )
                        continue

                    updated_count += 1
                    if not dry_run:
                        for key, value in payload.items():
                            setattr(existing, key, value)
                        existing.save()
                    self.stdout.write(self.style.SUCCESS(f"Row {row_index}: updated '{payload['title']}'"))
                    continue

                created_count += 1
                if not dry_run:
                    Project.objects.create(**payload)
                self.stdout.write(self.style.SUCCESS(f"Row {row_index}: created '{payload['title']}'"))

        mode = "DRY RUN" if dry_run else "IMPORT"
        self.stdout.write("-" * 72)
        self.stdout.write(
            self.style.NOTICE(
                f"{mode} summary | created={created_count} updated={updated_count} "
                f"skipped={skipped_count} errors={error_count}"
            )
        )

        if error_count:
            raise CommandError("Import finished with errors. Fix rows and run again.")

    def _build_payload(self, row, row_index):
        for col in REQUIRED_COLUMNS:
            if not row.get(col):
                raise CommandError(f"Row {row_index}: '{col}' is required.")

        skill_level = self._normalize_skill_level(row["skill_level"], row_index)
        required_plan = self._normalize_plan(row["required_plan"], row_index)

        payload = {
            "title": row["title"],
            "description": row["description"],
            "field": row["field"],
            "target_role": row["target_role"],
            "skill_level": skill_level,
            "required_plan": required_plan,
            "tech_preference": row["tech_preference"],
            "learning_goal": row["learning_goal"],
            "interest_tags": row["interest_tags"],
            "learning_objectives": row.get("learning_objectives", ""),
            "resources": row.get("resources", ""),
            "task_checklist": row.get("task_checklist", ""),
            "detailed_roadmap": row.get("detailed_roadmap", ""),
            "premium_hints": row.get("premium_hints", ""),
        }

        return payload

    def _normalize_skill_level(self, value, row_index):
        key = str(value).strip().lower()
        normalized = SKILL_LEVEL_NORMALIZATION.get(key)
        if not normalized:
            valid = ", ".join(SKILL_LEVEL_NORMALIZATION.keys())
            raise CommandError(f"Row {row_index}: invalid skill_level '{value}'. Valid: {valid}")
        return normalized

    def _normalize_plan(self, value, row_index):
        key = str(value).strip().lower()
        normalized = PLAN_NORMALIZATION.get(key)
        if not normalized:
            valid = ", ".join(sorted(PLAN_NORMALIZATION.keys()))
            raise CommandError(f"Row {row_index}: invalid required_plan '{value}'. Valid: {valid}")
        return normalized
