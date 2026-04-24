import os
import sys
from pathlib import Path
from django.db.models import Count

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from users.models import Project

lines = ["TOTAL_BY_FIELD"]
for row in Project.objects.values("field").annotate(c=Count("id")).order_by("field"):
    lines.append(f"{row['field']}: {row['c']}")

lines.append("")
lines.append("EXPLORER_BY_FIELD")
for row in (
    Project.objects.filter(required_plan="explorer")
    .values("field")
    .annotate(c=Count("id"))
    .order_by("field")
):
    lines.append(f"{row['field']}: {row['c']}")

out_path = PROJECT_ROOT / "data" / "_category_counts.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
