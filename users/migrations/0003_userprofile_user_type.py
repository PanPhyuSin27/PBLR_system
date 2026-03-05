from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_project_templates"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="user_type",
            field=models.CharField(choices=[("normal", "Normal"), ("premium", "Premium")], default="normal", max_length=20),
        ),
    ]
