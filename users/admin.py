from django.contrib import admin, messages
from django.utils import timezone
from .models import Plan, PremiumRequest, Project, Subscription, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "field", "target_role", "skill_level")
	list_filter = ("skill_level",)
	search_fields = ("user__username", "user__email", "field", "target_role")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
	list_display = ("name", "price")
	search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ("title", "required_plan", "field", "target_role", "skill_level", "tech_preference")
	list_filter = ("required_plan", "field", "skill_level", "target_role")
	search_fields = ("title", "description", "field", "target_role", "tech_preference", "learning_goal", "interest_tags", "required_plan")
	fieldsets = (
		("Core", {
			"fields": (
				"title",
				"description",
				"field",
				"target_role",
				"skill_level",
				"required_plan",
			)
		}),
		("Matching", {
			"fields": ("tech_preference", "learning_goal", "interest_tags")
		}),
		("Workspace Content", {
			"fields": (
				"learning_objectives",
				"resources",
				"task_checklist",
				"detailed_roadmap",
				"premium_hints",
			)
		}),
	)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
	list_display = ("user", "plan", "start_date", "end_date", "is_active")
	list_filter = ("plan", "is_active")
	search_fields = ("user__username", "user__email", "plan__name")


@admin.register(PremiumRequest)
class PremiumRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "plan", "status", "requested_at", "reviewed_at")
	list_filter = ("status",)
	search_fields = ("user__username", "user__email", "plan__name")
	actions = ["approve_requests", "reject_requests"]

	def approve_requests(self, request, queryset):
		fallback_plan = Plan.objects.filter(name__iexact="Pro Monthly").first()
		if not fallback_plan:
			fallback_plan = Plan.objects.filter(price__gt=0).order_by("price", "id").first()
		if not fallback_plan:
			self.message_user(request, "Create a paid plan first (e.g., Pro Monthly).", level=messages.ERROR)
			return
		count = 0
		for req in queryset.filter(status="pending"):
			selected_plan = req.plan if req.plan and req.plan.price > 0 else fallback_plan
			duration_days = 365 if selected_plan.name.lower().strip() == "pro yearly" else 30
			Subscription.objects.filter(user=req.user, is_active=True).update(is_active=False)
			Subscription.objects.create(
				user=req.user,
				plan=selected_plan,
				start_date=timezone.now().date(),
				end_date=timezone.now().date() + timezone.timedelta(days=duration_days),
				is_active=True,
			)
			req.status = "approved"
			req.reviewed_at = timezone.now()
			req.save()
			count += 1
		self.message_user(request, f"Approved {count} request(s).", level=messages.SUCCESS)

	def reject_requests(self, request, queryset):
		count = 0
		for req in queryset.filter(status="pending"):
			req.status = "rejected"
			req.reviewed_at = timezone.now()
			req.save()
			count += 1
		self.message_user(request, f"Rejected {count} request(s).", level=messages.WARNING)
