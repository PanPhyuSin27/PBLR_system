from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_remove_userprofile_user_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="PremiumRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, to="auth.user")),
            ],
            options={"ordering": ["-requested_at", "-id"]},
        ),
    ]
