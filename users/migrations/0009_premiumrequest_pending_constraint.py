from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_seed_subscription_plans"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="premiumrequest",
            constraint=models.UniqueConstraint(
                condition=Q(("status", "pending")),
                fields=("user",),
                name="users_one_pending_premium_request_per_user",
            ),
        ),
    ]
