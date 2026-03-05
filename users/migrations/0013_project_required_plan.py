from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_remove_project_template_system"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="required_plan",
            field=models.CharField(
                choices=[
                    ("explorer", "Explorer (Free)"),
                    ("pro_monthly", "Pro Monthly"),
                    ("pro_yearly", "Pro Yearly"),
                ],
                default="explorer",
                max_length=20,
            ),
        ),
    ]
