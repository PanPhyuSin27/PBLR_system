from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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
    profile_picture = models.FileField(upload_to="profile_pictures/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    features = models.TextField(blank=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date", "-id"]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after start date.")
        if self.is_active:
            qs = Subscription.objects.filter(user=self.user, is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("User already has an active subscription.")

    def save(self, *args, **kwargs):
        if self.end_date and self.end_date < timezone.now().date():
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.user} - {self.plan} ({status})"


class PremiumRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("Plan", on_delete=models.PROTECT, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="pending"),
                name="users_one_pending_premium_request_per_user",
            )
        ]

    def clean(self):
        if self.status == "pending":
            qs = PremiumRequest.objects.filter(user=self.user, status="pending")
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("User already has a pending premium request.")

    def __str__(self):
        return f"{self.user} - {self.status}"


class Project(models.Model):
    SKILL_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    PLAN_ACCESS_CHOICES = [
        ("explorer", "Explorer (Free)"),
        ("pro_monthly", "Pro Monthly"),
        ("pro_yearly", "Pro Yearly"),
    ]

    title = models.CharField(max_length=140)
    description = models.TextField()
    field = models.CharField(max_length=100)
    target_role = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES)
    required_plan = models.CharField(max_length=20, choices=PLAN_ACCESS_CHOICES, default="explorer")
    tech_preference = models.CharField(max_length=140)
    learning_goal = models.CharField(max_length=140)
    interest_tags = models.CharField(max_length=220, help_text="Comma separated tags")
    learning_objectives = models.TextField(blank=True)
    resources = models.TextField(blank=True, help_text="Optional resources. One per line. Use 'Title | URL' or plain URL.")
    task_checklist = models.TextField(blank=True, help_text="Checklist tasks, one per line.")
    detailed_roadmap = models.TextField(blank=True)
    github_starter_template = models.URLField(blank=True)
    premium_hints = models.TextField(blank=True, help_text="Premium hints, one per line.")

    class Meta:
        ordering = ["title", "id"]

    def __str__(self):
        return self.title