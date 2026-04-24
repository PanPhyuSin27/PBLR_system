from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_remove_project_github_starter_template"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyRecommendationUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usage_date", models.DateField(default=django.utils.timezone.localdate)),
                ("count", models.PositiveIntegerField(default=0)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-usage_date", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="dailyrecommendationusage",
            constraint=models.UniqueConstraint(fields=("user", "usage_date"), name="users_unique_daily_reco_usage"),
        ),
    ]
