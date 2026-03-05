from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0011_project"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ProjectTask",
        ),
        migrations.DeleteModel(
            name="ProjectPhase",
        ),
        migrations.DeleteModel(
            name="ProjectTemplate",
        ),
    ]
