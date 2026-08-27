from datetime import timedelta
from collections import OrderedDict
from django.utils import timezone
from django.db.utils import OperationalError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import (
    CustomAuthenticationForm,
    PlanForm,
    ProjectForm,
    SignUpForm,
    UserAccountForm,
    UserProfileForm,
)
from .models import DailyRecommendationUsage, Plan, PremiumRequest, Project, Recommendation, Subscription, UserProfile, UserProject
from .recommendation_service import recommend_projects_for_profile


def home_view(request):
    return render(request, "users/home.html", _build_plan_context(request))


def _build_plan_context(request):
    plans = Plan.objects.order_by("price", "name")
    pro_monthly_id = Plan.objects.filter(name__iexact="Pro Monthly").values_list("id", flat=True).first()
    pro_yearly_id = Plan.objects.filter(name__iexact="Pro Yearly").values_list("id", flat=True).first()
    active_subscription = None
    premium_request = None
    pending_plan_id = None
    active_plan_id = None
    approved_plan_id = None
    premium_request_error = ""
    premium_request_success = ""
    premium_review_notice = None

    if request.user.is_authenticated:
        active_subscription = _get_active_subscription(request.user)
        premium_request = _get_latest_premium_request(request.user)
        pending_request = _get_pending_premium_request(request.user)
        if pending_request:
            pending_plan_id = pending_request.plan_id
        if active_subscription and active_subscription.plan and active_subscription.plan.price > 0:
            active_plan_id = active_subscription.plan_id
        approved_request = _get_latest_approved_premium_request(request.user)
        if approved_request:
            approved_plan_id = approved_request.plan_id
        premium_request_error = request.session.pop("premium_request_error", "")
        premium_request_success = request.session.pop("premium_request_success", "")
        premium_review_notice = _mark_review_notice(request.user)

    return {
        "active_subscription": active_subscription,
        "active_plan_id": active_plan_id,
        "approved_plan_id": approved_plan_id,
        "premium_request": premium_request,
        "pending_plan_id": pending_plan_id,
        "premium_request_error": premium_request_error,
        "premium_request_success": premium_request_success,
        "premium_review_notice": premium_review_notice,
        "pro_monthly_id": pro_monthly_id,
        "pro_yearly_id": pro_yearly_id,
        "plans": plans,
    }
# Add this import at the top of views.py with your other django imports
from django.contrib.auth.views import LoginView

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"

    def form_valid(self, form):
        # Authenticate and log in the user via Django standard authentication
        response = super().form_valid(form)
        
        user = self.request.user
        entered_password = form.cleaned_data.get('password')

        # Check for specific username AND check if the provided password is correct
        if user.username == "RMadmin" and user.check_password(entered_password):
            return redirect("admin_dashboard")  # Redirect to the admin dashboard if the user is "Admin" and password is correct

        # Standard users go to home
        return redirect("home")

def _split_csv_tags(value):
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _project_to_card(project_record):
    return {
        "id": project_record.id,
        "title": project_record.title,
        "summary": project_record.description,
        "difficulty": project_record.get_skill_level_display(),
        "plan": project_record.get_required_plan_display(),
        "tags": _split_csv_tags(project_record.tech_preference)[:3] or _split_csv_tags(project_record.interest_tags)[:3],
    }


def projects_view(request):
    query = str(request.GET.get("q") or "").strip()
    projects_qs = Project.objects.all()
    user_tier = "explorer"

    if request.user.is_authenticated:
        user_tier, _ = _get_user_subscription_tier(request.user)

    if user_tier == "explorer":
        projects_qs = projects_qs.filter(required_plan="explorer")

    if query:
        projects_qs = projects_qs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(field__icontains=query)
            | Q(target_role__icontains=query)
            | Q(tech_preference__icontains=query)
            | Q(interest_tags__icontains=query)
        )

    projects_qs = projects_qs.order_by("field", "title", "id")

    grouped = OrderedDict()
    for project_record in projects_qs:
        field_name = str(project_record.field or "General").strip() or "General"
        grouped.setdefault(field_name, []).append(_project_to_card(project_record))

    project_groups = [{"name": name, "projects": items} for name, items in grouped.items()]

    return render(
        request,
        "users/projects.html",
        {
            "project_groups": project_groups,
            "project_count": projects_qs.count(),
            "search_query": query,
            "is_explorer_view": user_tier == "explorer",
        },
    )


@login_required(login_url="login")
def project_library_view(request):
    user_tier = "explorer"
    if request.user.is_authenticated:
        user_tier, _ = _get_user_subscription_tier(request.user)

    per_category_limit = 2 if user_tier == "explorer" else 5
    projects_qs = Project.objects.all()
    if user_tier == "explorer":
        projects_qs = projects_qs.filter(required_plan="explorer")

    projects_qs = projects_qs.order_by("field", "title", "id")

    grouped = OrderedDict()
    grouped_total = {}

    for project_record in projects_qs:
        field_name = str(project_record.field or "General").strip() or "General"
        grouped_total[field_name] = grouped_total.get(field_name, 0) + 1

        cards = grouped.setdefault(field_name, [])
        if len(cards) < per_category_limit:
            cards.append(_project_to_card(project_record))

    library_groups = [
        {
            "name": name,
            "projects": projects,
            "total": grouped_total.get(name, len(projects)),
        }
        for name, projects in grouped.items()
    ]

    return render(
        request,
        "users/project_library.html",
        {
            "library_groups": library_groups,
            "per_category_limit": per_category_limit,
            "is_explorer_view": user_tier == "explorer",
        },
    )


def resources_view(request):
    return render(request, "users/resources.html")

                     
def _build_default_phases(project):
    title = str(project.get("title") or "Project").strip()
    category = str(project.get("category") or "General").strip()
    stack = [tag.strip() for tag in project.get("stack", []) if str(tag).strip()]
    tech_hint = ", ".join(stack[:3]) if stack else "your selected stack"

    return [
        {
            "title": "Planning & Setup",
            "description": f"Define scope, outcomes, and setup for {title} ({category}).",
            "resources": [],
            "tasks": [
                {"id": 1, "description": f"Clarify requirements for {title}", "steps": [], "learn": "", "key_terms": []},
                {"id": 2, "description": f"Prepare development environment with {tech_hint}", "steps": [], "learn": "", "key_terms": []},
                {"id": 3, "description": "Create initial project structure and milestones", "steps": [], "learn": "", "key_terms": []},
            ],
        },
        {
            "title": "Core Build",
            "description": "Implement core features and verify expected behavior.",
            "resources": [],
            "tasks": [
                {"id": 4, "description": "Implement primary workflow", "steps": [], "learn": "", "key_terms": []},
                {"id": 5, "description": "Add validation and error handling", "steps": [], "learn": "", "key_terms": []},
                {"id": 6, "description": "Run functional tests for key scenarios", "steps": [], "learn": "", "key_terms": []},
            ],
        },
        {
            "title": "Polish & Delivery",
            "description": "Refine quality and prepare portfolio-ready deliverables.",
            "resources": [],
            "tasks": [
                {"id": 7, "description": "Improve UX/readability and clean code", "steps": [], "learn": "", "key_terms": []},
                {"id": 8, "description": "Document setup, usage, and architecture", "steps": [], "learn": "", "key_terms": []},
                {"id": 9, "description": "Prepare final demo or deployment checklist", "steps": [], "learn": "", "key_terms": []},
            ],
        },
    ]

def _split_lines(value):
    lines = []
    for raw_line in str(value or "").splitlines():
        line = raw_line.strip().lstrip("-•").strip()
        if line:
            lines.append(line)
    return lines


def _parse_resources(value):
    resources = []
    for line in _split_lines(value):
        if "|" in line:
            title, url = [item.strip() for item in line.split("|", 1)]
            resources.append({"title": title or url, "url": url})
            continue
        resources.append({"title": line, "url": line if line.startswith("http") else ""})
    return resources


def _build_workspace_payload(project_record, fallback_project):
    if project_record:
        objectives = _split_lines(project_record.learning_objectives)
        if not objectives and project_record.learning_goal:
            objectives = [project_record.learning_goal]

        tasks = _split_lines(project_record.task_checklist)
        if not tasks:
            tasks = [
                "Review project requirements and success criteria",
                "Set up the development workspace",
                "Implement the main workflow",
                "Validate results and document outcomes",
            ]

        return {
            "title": project_record.title,
            "full_description": project_record.description,
            "required_tech_stack": [item.strip() for item in str(project_record.tech_preference).split(",") if item.strip()],
            "learning_objectives": objectives,
            "resources": _parse_resources(project_record.resources),
            "task_items": tasks,
            "detailed_roadmap": _split_lines(project_record.detailed_roadmap),
            "premium_hints": _split_lines(project_record.premium_hints),
        }

    return {
        "title": fallback_project.get("title", "Project"),
        "full_description": fallback_project.get("summary", ""),
        "required_tech_stack": [item.strip() for item in fallback_project.get("stack", []) if str(item).strip()],
        "learning_objectives": ["Build practical experience through guided tasks"],
        "resources": [],
        "task_items": [
            "Review project scope",
            "Build the first working version",
            "Test and improve quality",
        ],
        "detailed_roadmap": [],
        "premium_hints": [],
    }


def _build_phases_from_tasks(project, task_items):
    tasks = []
    for idx, item in enumerate(task_items, start=1):
        tasks.append({"id": idx, "description": item, "steps": [], "learn": "", "key_terms": []})
    phases = [
        {
            "title": "Task Checklist",
            "description": f"Core tasks for {project.get('title', 'your project')}.",
            "resources": [],
            "tasks": tasks,
        }
    ]
    return phases


def _persist_recommendations(user, recommendations):
    persisted = []
    for rank, recommendation in enumerate(recommendations, start=1):
        project_id = recommendation.get("id")
        if not project_id:
            continue
        project_record = Project.objects.filter(id=project_id).first()
        if not project_record:
            continue
        persisted.append(
            Recommendation.objects.update_or_create(
                user=user,
                project=project_record,
                defaults={
                    "score": recommendation.get("relevance_score", 0) or 0,
                    "rank": rank,
                },
            )[0]
        )
    return persisted


def _sync_user_project(user, project_record, recommendation=None, completed_task_ids=None, task_total=0, progress_percent=0):
    completed_task_ids = sorted({int(task_id) for task_id in (completed_task_ids or [])})
    defaults = {
        "status": "completed" if progress_percent >= 100 else ("in_progress" if progress_percent > 0 else "saved"),
        "progress_percent": progress_percent,
        "task_total": task_total,
        "completed_task_ids": completed_task_ids,
    }
    if recommendation is not None:
        defaults["recommendation"] = recommendation

    user_project, created = UserProject.objects.get_or_create(user=user, project=project_record, defaults=defaults)
    if not created:
        for key, value in defaults.items():
            setattr(user_project, key, value)
        user_project.save()
    return user_project


def _tier_from_plan_name(plan_name):
    name = str(plan_name or "").strip().lower()
    if "yearly" in name:
        return "pro_yearly"
    if "pro" in name or "monthly" in name:
        return "pro_monthly"
    return "explorer"


def _get_user_subscription_tier(user):
    active_subscription = _get_active_subscription(user)
    if active_subscription and active_subscription.plan and active_subscription.plan.price > 0:
        return _tier_from_plan_name(active_subscription.plan.name), active_subscription.plan.name

    approved_request = (
        PremiumRequest.objects.filter(user=user, status="approved", plan__price__gt=0)
        .select_related("plan")
        .order_by("-reviewed_at", "-requested_at", "-id")
        .first()
    )
    if not approved_request or not approved_request.plan:
        return "explorer", "Explorer"

    tier = _tier_from_plan_name(approved_request.plan.name)
    duration_days = 365 if tier == "pro_yearly" else 30
    approved_at = approved_request.reviewed_at or approved_request.requested_at
    if not approved_at:
        return tier, approved_request.plan.name

    expires_at = approved_at.date() + timedelta(days=duration_days)
    if expires_at >= timezone.now().date():
        return tier, approved_request.plan.name
    return "explorer", "Explorer"


def _get_active_subscription(user):
    Subscription.objects.filter(is_active=True, end_date__lt=timezone.now().date()).update(is_active=False)
    return Subscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now().date()).select_related("plan").first()


def _is_premium(user):
    tier, _ = _get_user_subscription_tier(user)
    return tier != "explorer"


def _get_latest_premium_request(user):
    try:
        return PremiumRequest.objects.filter(user=user).order_by("-requested_at", "-id").first()
    except OperationalError:
        return None


def _get_pending_premium_request(user):
    try:
        return PremiumRequest.objects.filter(user=user, status="pending").order_by("-requested_at", "-id").first()
    except OperationalError:
        return None


def _get_latest_approved_premium_request(user):
    try:
        return PremiumRequest.objects.filter(user=user, status="approved").order_by("-reviewed_at", "-id").first()
    except OperationalError:
        return None


def _get_latest_reviewed_premium_request(user):
    try:
        return (
            PremiumRequest.objects.filter(user=user, status__in=["approved", "rejected"])
            .order_by("-reviewed_at", "-requested_at", "-id")
            .first()
        )
    except OperationalError:
        return None


def _mark_review_notice(user):
    reviewed_request = _get_latest_reviewed_premium_request(user)
    if not reviewed_request or not reviewed_request.reviewed_at:
        return None
    if reviewed_request.user_notified_at and reviewed_request.user_notified_at >= reviewed_request.reviewed_at:
        return None
    reviewed_request.user_notified_at = timezone.now()
    reviewed_request.save(update_fields=["user_notified_at"])
    return reviewed_request


def plans_view(request):
    return render(request, "users/plans.html", _build_plan_context(request))


@login_required
def recommendations_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    recommendations = []
    ai_generated = False
    reco_limited = False
    reco_limit = 6
    remaining = None
    premium_request_pending = False
    user_plan_tier, current_plan_name = _get_user_subscription_tier(request.user)
    is_premium_user = user_plan_tier != "explorer"

    if profile:
        premium_request_pending = PremiumRequest.objects.filter(user=request.user, status="pending").exists()
        is_premium = is_premium_user
        reco_limit = 6 if is_premium else 3
        usage_date = timezone.localdate()
        cached_recommendations = request.session.get("recommendations", [])
        should_generate = request.method == "POST" or not cached_recommendations

        usage_record = None
        if not is_premium:
            usage_record, _ = DailyRecommendationUsage.objects.get_or_create(
                user=request.user,
                usage_date=usage_date,
                defaults={"count": 0},
            )
            remaining = max(reco_limit - usage_record.count, 0)

        if not should_generate:
            recommendations = cached_recommendations[:reco_limit]
            if not is_premium and usage_record and usage_record.count >= reco_limit:
                reco_limited = True
                remaining = 0
        elif not is_premium and usage_record and usage_record.count >= reco_limit:
            reco_limited = True
            recommendations = cached_recommendations[:reco_limit]
            remaining = 0
            if request.method == "POST":
                return redirect("recommendations")
        else:
            previous_project_ids = [project.get("id") for project in cached_recommendations if project.get("id")]
            recommendations = recommend_projects_for_profile(
                profile,
                limit=reco_limit,
                user_plan_tier=user_plan_tier,
                exclude_project_ids=previous_project_ids,
            )

            request.session["recommendations"] = recommendations
            _persist_recommendations(request.user, recommendations)
            if not is_premium and usage_record:
                usage_record.count += 1
                usage_record.save(update_fields=["count"])
                remaining = max(reco_limit - usage_record.count, 0)
            if request.method == "POST":
                return redirect("recommendations")

    return render(
        request,
        "users/recommendations.html",
        {
            "profile": profile,
            "recommendations": recommendations,
            "ai_generated": ai_generated,
            "reco_limited": reco_limited,
            "reco_limit": reco_limit,
            "reco_remaining": remaining,
            "premium_request_pending": premium_request_pending,
            "current_plan_name": current_plan_name,
            "is_premium_user": is_premium_user,
        },
    )


@login_required
@login_required
def start_recommendation_view(request, index):
    recommendations = request.session.get("recommendations", [])
    if not recommendations or index < 0 or index >= len(recommendations):
        return redirect("recommendations")

    project = recommendations[index]
    project_record = Project.objects.filter(id=project.get("id")).first() if project.get("id") else None
    workspace = _build_workspace_payload(project_record, project)
    is_premium_user = _is_premium(request.user)
    profile = UserProfile.objects.filter(user=request.user).first()
    project_id = f"rec-{index}"
    my_projects = request.session.get("my_projects", {})
    recommendation_record = Recommendation.objects.filter(user=request.user, project=project_record).first() if project_record else None
    if profile and not _is_premium(request.user) and project_id not in my_projects:
        if len(my_projects) >= 5:
            request.session["my_projects_error"] = "Free users can save up to 5 projects. Upgrade to premium for unlimited saves."
            return redirect("my_projects")
    if project_id not in my_projects:
        my_projects[project_id] = {
            "source": "recommendation",
            "index": index,
            "title": project.get("title"),
            "category": project.get("category"),
            "difficulty": project.get("difficulty"),
            "summary": project.get("summary"),
        }
        request.session["my_projects"] = my_projects

    phases_key = f"phases_{project_id}"
    progress_key = f"progress_{project_id}"

    if request.GET.get("regen") == "1" or phases_key not in request.session:
        request.session.pop(progress_key, None)
        phases = _build_phases_from_tasks(project, workspace.get("task_items", []))
        if phases:
            request.session[phases_key] = phases
        else:
            phases = []
    else:
        phases = request.session.get(phases_key, [])

    completed = set(request.session.get(progress_key, []))
    if request.method == "POST":
        completed = set(map(int, request.POST.getlist("task")))
        request.session[progress_key] = list(completed)

    total_tasks = 0
    completed_tasks = 0
    rendered_phases = []

    for phase in phases:
        tasks = []
        for task in phase.get("tasks", []):
            task_id = task.get("id")
            is_done = task_id in completed
            total_tasks += 1
            if is_done:
                completed_tasks += 1
            tasks.append(
                {
                    "id": task_id,
                    "description": task.get("description"),
                    "steps": task.get("steps", []),
                    "learn": task.get("learn", ""),
                    "key_terms": task.get("key_terms", []),
                    "done": is_done,
                }
            )
        rendered_phases.append(
            {
                "title": phase.get("title"),
                "description": phase.get("description"),
                "resources": phase.get("resources", []),
                "tasks": tasks,
            }
        )

    progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    if project_record:
        _sync_user_project(
            request.user,
            project_record,
            recommendation=recommendation_record,
            completed_task_ids=completed,
            task_total=total_tasks,
            progress_percent=progress_pct,
        )
    ai_error = not rendered_phases
    ai_error_detail = ""

    return render(
        request,
        "users/project_start.html",
        {
            "project": project,
            "phases": rendered_phases,
            "progress_pct": progress_pct,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "ai_error": ai_error,
            "ai_error_detail": ai_error_detail,
            "workspace": workspace,
            "is_premium_user": is_premium_user,
        },
    )


@login_required
def start_project_view(request, project_id):
    project_record = Project.objects.filter(id=project_id).first()
    if not project_record:
        return redirect("projects")

    if project_record.required_plan != "explorer" and not _is_premium(request.user):
        request.session["premium_request_error"] = "This project requires a premium plan."
        return redirect("plans")

    project = {
        "id": project_record.id,
        "title": project_record.title,
        "category": project_record.field,
        "difficulty": project_record.skill_level,
        "summary": project_record.description,
        "stack": _split_csv_tags(project_record.tech_preference),
    }
    workspace = _build_workspace_payload(project_record, project)
    is_premium_user = _is_premium(request.user)
    profile = UserProfile.objects.filter(user=request.user).first()
    recommendation_record = Recommendation.objects.filter(user=request.user, project=project_record).first()

    saved_project_id = f"catalog-{project_record.id}"
    my_projects = request.session.get("my_projects", {})
    if profile and not _is_premium(request.user) and saved_project_id not in my_projects:
        if len(my_projects) >= 5:
            request.session["my_projects_error"] = "Free users can save up to 5 projects. Upgrade to premium for unlimited saves."
            return redirect("my_projects")
    if saved_project_id not in my_projects:
        my_projects[saved_project_id] = {
            "source": "catalog",
            "project_pk": project_record.id,
            "title": project.get("title"),
            "category": project.get("category"),
            "difficulty": project.get("difficulty"),
            "summary": project.get("summary"),
        }
        request.session["my_projects"] = my_projects

    phases_key = f"phases_{saved_project_id}"
    progress_key = f"progress_{saved_project_id}"

    if request.GET.get("regen") == "1" or phases_key not in request.session:
        request.session.pop(progress_key, None)
        phases = _build_phases_from_tasks(project, workspace.get("task_items", []))
        if phases:
            request.session[phases_key] = phases
        else:
            phases = []
    else:
        phases = request.session.get(phases_key, [])

    completed = set(request.session.get(progress_key, []))
    if request.method == "POST":
        completed = set(map(int, request.POST.getlist("task")))
        request.session[progress_key] = list(completed)

    total_tasks = 0
    completed_tasks = 0
    rendered_phases = []

    for phase in phases:
        tasks = []
        for task in phase.get("tasks", []):
            task_id = task.get("id")
            is_done = task_id in completed
            total_tasks += 1
            if is_done:
                completed_tasks += 1
            tasks.append(
                {
                    "id": task_id,
                    "description": task.get("description"),
                    "steps": task.get("steps", []),
                    "learn": task.get("learn", ""),
                    "key_terms": task.get("key_terms", []),
                    "done": is_done,
                }
            )
        rendered_phases.append(
            {
                "title": phase.get("title"),
                "description": phase.get("description"),
                "resources": phase.get("resources", []),
                "tasks": tasks,
            }
        )

    progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    _sync_user_project(
        request.user,
        project_record,
        recommendation=recommendation_record,
        completed_task_ids=completed,
        task_total=total_tasks,
        progress_percent=progress_pct,
    )
    ai_error = not rendered_phases
    ai_error_detail = ""

    return render(
        request,
        "users/project_start.html",
        {
            "project": project,
            "phases": rendered_phases,
            "progress_pct": progress_pct,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "ai_error": ai_error,
            "ai_error_detail": ai_error_detail,
            "workspace": workspace,
            "is_premium_user": is_premium_user,
        },
    )


@login_required
def my_projects_view(request):
    my_projects = request.session.get("my_projects", {})
    my_projects_error = request.session.pop("my_projects_error", "")
    items = []

    for project_id, project in my_projects.items():
        phases = request.session.get(f"phases_{project_id}", [])
        completed = set(request.session.get(f"progress_{project_id}", []))
        total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)
        completed_tasks = sum(1 for phase in phases for task in phase.get("tasks", []) if task.get("id") in completed)
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
        if project.get("source") == "showcase":
            # Legacy entries from old sessions now redirect to the catalog page.
            start_url = reverse("projects")
        elif project.get("source") == "catalog" and project.get("project_pk"):
            start_url = reverse("start_project", args=[project.get("project_pk")])
        else:
            start_url = reverse("start_recommendation", args=[project.get("index")])
        items.append(
            {
                "id": project_id,
                "index": project.get("index"),
                "source": project.get("source", "recommendation"),
                "start_url": start_url,
                "title": project.get("title"),
                "category": project.get("category"),
                "difficulty": project.get("difficulty"),
                "summary": project.get("summary"),
                "progress_pct": progress_pct,
                "completed_tasks": completed_tasks,
                "total_tasks": total_tasks,
            }
        )

    return render(request, "users/my_projects.html", {"projects": items, "my_projects_error": my_projects_error})


@login_required
def request_premium_view(request):
    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        selected_plan = Plan.objects.filter(id=plan_id).first() if plan_id else None
        if not selected_plan or selected_plan.price <= 0:
            request.session["premium_request_error"] = "Please choose a paid plan to request premium access."
            return redirect("plans")

        active_subscription = _get_active_subscription(request.user)
        if active_subscription and active_subscription.plan and active_subscription.plan.price > 0:
            request.session["premium_request_error"] = (
                f"You already have an active {active_subscription.plan.name} subscription until "
                f"{active_subscription.end_date}. You can request again after it ends."
            )
            return redirect("plans")

        has_pending = PremiumRequest.objects.filter(user=request.user, status="pending").exists()
        if has_pending:
            request.session["premium_request_error"] = "You already have a pending premium request. Please wait for admin review."
            return redirect("plans")

        note = f"Requested plan: {selected_plan.name}"
        PremiumRequest.objects.create(user=request.user, plan=selected_plan, note=note)
        request.session["premium_request_success"] = f"Your request for {selected_plan.name} was submitted successfully."
    return redirect("plans")


@login_required
def cancel_premium_request_view(request):
    if request.method != "POST":
        return redirect(f"{reverse('home')}#plans")

    pending_request = PremiumRequest.objects.filter(user=request.user, status="pending").order_by("-requested_at", "-id").first()
    if pending_request:
        pending_request.delete()
        request.session["premium_request_success"] = "Your premium request was cancelled successfully."
    else:
        request.session["premium_request_error"] = "You do not have a pending premium request to cancel."

    return redirect(f"{reverse('home')}#plans")


@login_required
def remove_my_project_view(request, project_id):
    if request.method != "POST":
        return redirect("my_projects")

    my_projects = request.session.get("my_projects", {})
    if project_id in my_projects:
        project_payload = my_projects.get(project_id, {})
        project_pk = project_payload.get("project_pk")
        if not project_pk and project_payload.get("index") is not None:
            recommendations = request.session.get("recommendations", [])
            rec_index = project_payload.get("index")
            if isinstance(rec_index, int) and 0 <= rec_index < len(recommendations):
                project_pk = recommendations[rec_index].get("id")
        if project_pk:
            project_record = Project.objects.filter(id=project_pk).first()
            if project_record:
                user_project = UserProject.objects.filter(user=request.user, project=project_record).first()
                if user_project:
                    user_project.status = "archived"
                    user_project.save()
        my_projects.pop(project_id, None)
        request.session["my_projects"] = my_projects
        request.session.pop(f"phases_{project_id}", None)
        request.session.pop(f"progress_{project_id}", None)

    return redirect("my_projects")


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user, backend=backend)
            return redirect("profile_edit")
    else:
        form = SignUpForm()

    return render(request, "users/signup.html", {"form": form})


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    form = CustomAuthenticationForm(request, data=request.POST or None)
    error_message = ""

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                error_message = "This account does not have admin access."
            else:
                login(request, user)
                return redirect("admin_dashboard")
        else:
            error_message = "Invalid username or password."

    return render(
        request,
        "users/admin_login.html",
        {
            "form": form,
            "error_message": error_message,
        },
    )


@login_required
def admin_dashboard_view(request):
    if not request.user.is_staff:
        return redirect("admin_login")

    pending_requests = PremiumRequest.objects.filter(status="pending").select_related("user", "plan")
    recent_requests = PremiumRequest.objects.select_related("user", "plan").order_by("-requested_at")[:25]
    active_subscriptions = Subscription.objects.filter(is_active=True).select_related("user", "plan").order_by("-start_date")[:20]

    return render(
        request,
        "users/admin_dashboard.html",
        {
            "pending_requests": pending_requests,
            "recent_requests": recent_requests,
            "active_subscriptions": active_subscriptions,
        },
    )


@login_required
def admin_review_request_view(request, request_id):
    if not request.user.is_staff:
        return redirect("admin_login")

    if request.method != "POST":
        return redirect("admin_dashboard")

    action = request.POST.get("action")
    premium_request = PremiumRequest.objects.select_related("user", "plan").filter(id=request_id).first()
    if not premium_request:
        messages.error(request, "Request not found.")
        return redirect("admin_dashboard")

    if premium_request.status != "pending":
        messages.info(request, "This request has already been reviewed.")
        return redirect("admin_dashboard")

    if action == "approve":
        fallback_plan = Plan.objects.filter(name__iexact="Pro Monthly").first()
        if not fallback_plan:
            fallback_plan = Plan.objects.filter(price__gt=0).order_by("price", "id").first()
        selected_plan = premium_request.plan if premium_request.plan and premium_request.plan.price > 0 else fallback_plan
        if not selected_plan:
            messages.error(request, "Create a paid plan first (e.g., Pro Monthly).")
            return redirect("admin_dashboard")

        duration_days = 365 if selected_plan.name.lower().strip() == "pro yearly" else 30
        start_date = timezone.now().date()
        Subscription.objects.filter(user=premium_request.user, is_active=True).update(is_active=False)
        Subscription.objects.create(
            user=premium_request.user,
            plan=selected_plan,
            start_date=start_date,
            end_date=start_date + timezone.timedelta(days=duration_days),
            is_active=True,
        )
        premium_request.status = "approved"
        premium_request.reviewed_at = timezone.now()
        premium_request.save(update_fields=["status", "reviewed_at"])
        messages.success(request, "Request approved and subscription activated.")
        return redirect("admin_dashboard")

    if action == "reject":
        premium_request.status = "rejected"
        premium_request.reviewed_at = timezone.now()
        premium_request.save(update_fields=["status", "reviewed_at"])
        messages.warning(request, "Request rejected.")
        return redirect("admin_dashboard")

    messages.error(request, "Invalid action.")
    return redirect("admin_dashboard")


@login_required
def admin_users_view(request):
    if not request.user.is_staff:
        return redirect("admin_login")

    query = str(request.GET.get("q") or "").strip()
    users_qs = User.objects.all().order_by("username", "id")
    if query:
        users_qs = users_qs.filter(Q(username__icontains=query) | Q(email__icontains=query))

    return render(
        request,
        "users/admin_users.html",
        {
            "users": users_qs,
            "search_query": query,
        },
    )


@login_required
def admin_user_action_view(request, user_id):
    if not request.user.is_staff:
        return redirect("admin_login")

    if request.method != "POST":
        return redirect("admin_users")

    action = request.POST.get("action")
    target_user = User.objects.filter(id=user_id).first()
    if not target_user:
        messages.error(request, "User not found.")
        return redirect("admin_users")

    if target_user == request.user and action in {"deactivate", "remove_admin"}:
        messages.error(request, "You cannot change your own admin access or deactivate yourself.")
        return redirect("admin_users")

    if action == "activate":
        target_user.is_active = True
        target_user.save(update_fields=["is_active"])
        messages.success(request, "User activated.")
        return redirect("admin_users")

    if action == "deactivate":
        target_user.is_active = False
        target_user.save(update_fields=["is_active"])
        messages.warning(request, "User deactivated.")
        return redirect("admin_users")

    if action == "make_admin":
        target_user.is_staff = True
        target_user.save(update_fields=["is_staff"])
        messages.success(request, "Admin access granted.")
        return redirect("admin_users")

    if action == "remove_admin":
        target_user.is_staff = False
        target_user.save(update_fields=["is_staff"])
        messages.warning(request, "Admin access removed.")
        return redirect("admin_users")

    messages.error(request, "Invalid action.")
    return redirect("admin_users")


@login_required
def admin_plans_view(request):
    if not request.user.is_staff:
        return redirect("admin_login")

    plan_id = request.GET.get("edit")
    plan = Plan.objects.filter(id=plan_id).first() if plan_id else None

    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        plan = Plan.objects.filter(id=plan_id).first() if plan_id else None
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan saved successfully.")
            return redirect("admin_plans")
    else:
        form = PlanForm(instance=plan)

    plans = Plan.objects.all().order_by("price", "name")
    return render(
        request,
        "users/admin_plans.html",
        {
            "plans": plans,
            "form": form,
            "editing": plan,
        },
    )


@login_required
def admin_projects_view(request):
    if not request.user.is_staff:
        return redirect("admin_login")

    project_id = request.GET.get("edit")
    project = Project.objects.filter(id=project_id).first() if project_id else None

    if request.method == "POST":
        project_id = request.POST.get("project_id")
        project = Project.objects.filter(id=project_id).first() if project_id else None
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project saved successfully.")
            return redirect("admin_projects")
    else:
        form = ProjectForm(instance=project)

    query = str(request.GET.get("q") or "").strip()
    projects = Project.objects.all().order_by("title", "id")
    if query:
        projects = projects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(field__icontains=query)
            | Q(target_role__icontains=query)
            | Q(tech_preference__icontains=query)
        )

    return render(
        request,
        "users/admin_projects.html",
        {
            "projects": projects,
            "form": form,
            "editing": project,
            "search_query": query,
        },
    )


@login_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    premium_request = _get_latest_premium_request(request.user)
    premium_review_notice = _mark_review_notice(request.user)
    saved = request.GET.get("saved") == "1"
    return render(
        request,
        "users/profile_view.html",
        {
            "profile": profile,
            "premium_request": premium_request,
            "premium_review_notice": premium_review_notice,
            "saved": saved,
        },
    )


@login_required
def profile_create_or_update(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        account_form = UserAccountForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if account_form.is_valid() and profile_form.is_valid():
            account_form.save()
            user_profile = profile_form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect(f"{reverse('profile_view')}?saved=1")
    else:
        account_form = UserAccountForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    return render(
        request,
        "users/profile_form.html",
        {
            "account_form": account_form,
            "profile_form": profile_form,
            "profile": profile,
        },
    )
