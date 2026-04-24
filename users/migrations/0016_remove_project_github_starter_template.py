from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0015_userprofile_profile_picture"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="github_starter_template",
        ),
    ]
