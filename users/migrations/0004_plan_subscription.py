from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_userprofile_user_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ("description", models.TextField(blank=True)),
                ("features", models.TextField(blank=True)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(default=django.utils.timezone.now)),
                ("end_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("plan", models.ForeignKey(on_delete=models.deletion.PROTECT, to="users.plan")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, to="auth.user")),
            ],
            options={"ordering": ["-start_date", "-id"]},
        ),
    ]
