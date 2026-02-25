from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    objects = None
    SKILL_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    LEARNING_STYLE_CHOICES = [
        ("step_by_step", "Step-by-step"),
        ("hands_on", "Hands-on"),
        ("visual_examples", "Visual + examples"),
        ("short_lessons", "Short lessons + practice"),
        ("guided_checklist", "Guided checklist"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    field = models.CharField(max_length=100)
    target_role = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES)
    tech_preference = models.CharField(max_length=100)
    learning_goal = models.CharField(max_length=100)
    interest_tags = models.CharField(max_length=200, help_text="Comma separated tags")
    learning_style = models.CharField(max_length=100, blank=True, null=True, choices=LEARNING_STYLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} Profile"

class ProjectTemplate(models.Model):
    category = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.category


class ProjectPhase(models.Model):
    template = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE, related_name="phases")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.template.category} - {self.title}"


class ProjectTask(models.Model):
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name="tasks")
    description = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.description