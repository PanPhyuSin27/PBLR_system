from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0017_dailyrecommendationusage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="learning_style",
        ),
    ]
