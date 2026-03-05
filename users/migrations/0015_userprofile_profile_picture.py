from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_project_workspace_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="profile_picture",
            field=models.FileField(blank=True, null=True, upload_to="profile_pictures/"),
        ),
    ]
