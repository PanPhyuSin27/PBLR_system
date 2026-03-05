from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_plan_subscription"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="user_type",
        ),
    ]
