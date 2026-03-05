from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0013_project_required_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="detailed_roadmap",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="project",
            name="github_starter_template",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="project",
            name="learning_objectives",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="project",
            name="premium_hints",
            field=models.TextField(blank=True, help_text="Premium hints, one per line."),
        ),
        migrations.AddField(
            model_name="project",
            name="resources",
            field=models.TextField(blank=True, help_text="Optional resources. One per line. Use 'Title | URL' or plain URL."),
        ),
        migrations.AddField(
            model_name="project",
            name="task_checklist",
            field=models.TextField(blank=True, help_text="Checklist tasks, one per line."),
        ),
    ]
