from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


PLAN_NAME_BY_CODE = {
    "explorer": "Explorer Plan (Free)",
    "pro_monthly": "Pro Monthly",
    "pro_yearly": "Pro Yearly",
}


def backfill_project_plans(apps, schema_editor):
    Project = apps.get_model("users", "Project")
    Plan = apps.get_model("users", "Plan")

    plans_by_name = {plan.name: plan for plan in Plan.objects.all()}

    for project in Project.objects.select_related("plan").all():
        if project.plan_id:
            continue
        plan_name = PLAN_NAME_BY_CODE.get(project.required_plan)
        if not plan_name:
            continue
        plan = plans_by_name.get(plan_name)
        if plan:
            project.plan = plan
            project.required_plan = project.required_plan or "explorer"
            project.save(update_fields=["plan", "required_plan"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0019_premiumrequest_user_notified_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="projects",
                to="users.plan",
            ),
        ),
        migrations.CreateModel(
            name="Recommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.FloatField(default=0)),
                ("rank", models.PositiveSmallIntegerField(default=1)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="users.project"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_recommendations", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["rank", "-score", "-updated_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="UserProject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("saved", "Saved"),
                            ("in_progress", "In progress"),
                            ("completed", "Completed"),
                            ("archived", "Archived"),
                        ],
                        default="saved",
                        max_length=20,
                    ),
                ),
                ("progress_percent", models.PositiveSmallIntegerField(default=0)),
                ("task_total", models.PositiveIntegerField(default=0)),
                ("completed_task_ids", models.JSONField(blank=True, default=list)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_projects", to="users.project"),
                ),
                (
                    "recommendation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="saved_projects",
                        to="users.recommendation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_projects", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-updated_at", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="recommendation",
            constraint=models.UniqueConstraint(fields=("user", "project"), name="users_unique_recommendation_per_project"),
        ),
        migrations.AddConstraint(
            model_name="userproject",
            constraint=models.UniqueConstraint(fields=("user", "project"), name="users_unique_user_project"),
        ),
        migrations.RunPython(backfill_project_plans, migrations.RunPython.noop),
    ]