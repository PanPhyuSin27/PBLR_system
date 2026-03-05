from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_premiumrequest_pending_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="premiumrequest",
            name="plan",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="users.plan"),
        ),
    ]
