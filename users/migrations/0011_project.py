from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0010_premiumrequest_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("description", models.TextField()),
                ("field", models.CharField(max_length=100)),
                ("target_role", models.CharField(max_length=100)),
                (
                    "skill_level",
                    models.CharField(
                        choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")],
                        max_length=20,
                    ),
                ),
                ("tech_preference", models.CharField(max_length=140)),
                ("learning_goal", models.CharField(max_length=140)),
                ("interest_tags", models.CharField(help_text="Comma separated tags", max_length=220)),
            ],
            options={
                "ordering": ["title", "id"],
            },
        ),
    ]
