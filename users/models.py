from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


PLAN_CODE_TO_NAME = {
    "explorer": "Explorer Plan (Free)",
    "pro_monthly": "Pro Monthly",
    "pro_yearly": "Pro Yearly",
}


class UserProfile(models.Model):
    objects = None
    SKILL_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    field = models.CharField(max_length=100)
    target_role = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES)
    tech_preference = models.CharField(max_length=100)
    learning_goal = models.CharField(max_length=100)
    interest_tags = models.CharField(max_length=200, help_text="Comma separated tags")
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
    user_notified_at = models.DateTimeField(blank=True, null=True)
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


class DailyRecommendationUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    usage_date = models.DateField(default=timezone.localdate)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-usage_date", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "usage_date"], name="users_unique_daily_reco_usage")
        ]

    def __str__(self):
        return f"{self.user} - {self.usage_date} ({self.count})"


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
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="projects", blank=True, null=True)
    required_plan = models.CharField(max_length=20, choices=PLAN_ACCESS_CHOICES, default="explorer")

    tech_preference = models.CharField(max_length=140)
    learning_goal = models.CharField(max_length=140)
    interest_tags = models.CharField(max_length=220, help_text="Comma separated tags")
    learning_objectives = models.TextField(blank=True)
    resources = models.TextField(blank=True, help_text="Optional resources. One per line. Use 'Title | URL' or plain URL.")
    task_checklist = models.TextField(blank=True, help_text="Checklist tasks, one per line.")
    detailed_roadmap = models.TextField(blank=True)
    premium_hints = models.TextField(blank=True, help_text="Premium hints, one per line.")

    class Meta:
        ordering = ["title", "id"]

    def _sync_plan_fields(self):
        if self.plan_id:
            plan_name = str(self.plan.name or "").strip().lower()
            if "pro yearly" in plan_name:
                self.required_plan = "pro_yearly"
            elif "pro monthly" in plan_name:
                self.required_plan = "pro_monthly"
            else:
                self.required_plan = "explorer"
        else:
            plan_name = PLAN_CODE_TO_NAME.get(self.required_plan)
            if plan_name:
                self.plan = Plan.objects.filter(name__iexact=plan_name).first()

    def save(self, *args, **kwargs):
        self._sync_plan_fields()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_recommendations")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="recommendations")
    score = models.FloatField(default=0)
    rank = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "-score", "-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="users_unique_recommendation_per_project")
        ]

    def __str__(self):
        return f"{self.user} -> {self.project} ({self.score})"


class UserProject(models.Model):
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_projects")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="user_projects")
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.SET_NULL,
        related_name="saved_projects",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="saved")
    progress_percent = models.PositiveSmallIntegerField(default=0)
    task_total = models.PositiveIntegerField(default=0)
    completed_task_ids = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["user", "project"], name="users_unique_user_project")]

    def save(self, *args, **kwargs):
        if self.progress_percent >= 100:
            self.progress_percent = 100
            self.status = "completed"
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.progress_percent > 0 and self.status == "saved":
            self.status = "in_progress"
            if not self.started_at:
                self.started_at = timezone.now()
        elif self.progress_percent > 0 and not self.started_at:
            self.started_at = timezone.now()

        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.project} ({self.status}, {self.progress_percent}%)"