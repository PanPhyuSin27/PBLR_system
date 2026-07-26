from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0018_remove_userprofile_learning_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="premiumrequest",
            name="user_notified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
