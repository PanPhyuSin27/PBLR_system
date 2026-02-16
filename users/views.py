import json
import os
import urllib.error
import urllib.request

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import SignUpForm, UserProfileForm
from .models import UserProfile


def home_view(request):
    return render(request, "users/home.html")


def projects_view(request):
    return render(request, "users/projects.html")


def _build_profile_payload(profile):
    return {
        "field": profile.field,
        "target_role": profile.target_role,
        "skill_level": profile.skill_level,
        "tech_preference": profile.tech_preference,
        "learning_goal": profile.learning_goal,
        "interest_tags": profile.interest_tags,
        "learning_style": profile.learning_style,
    }


def _fetch_ai_recommendations(profile, request):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return []

    prompt = (
        "You are a project recommendation engine. "
        "Return a JSON array of 6 project suggestions based on this user profile. "
        "Each item must include: title, category, difficulty (beginner/intermediate/advanced), "
        "summary (1 sentence), and stack (array of 3-5 short tags). "
        "Return only valid JSON, no extra text.\n\n"
        f"Profile: {json.dumps(_build_profile_payload(profile))}"
    )

    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": "You only respond with JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": request.build_absolute_uri("/"),
        "X-Title": "RecoMagic",
    }

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return []

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError):
        return []

    if not isinstance(parsed, list):
        return []

    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": item.get("title", "Untitled Project"),
                "category": item.get("category", "Custom Projects"),
                "difficulty": item.get("difficulty", "intermediate"),
                "summary": item.get("summary", ""),
                "stack": item.get("stack", []),
            }
        )
    return normalized


def _fetch_ai_phases(profile, project, request):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return []

    payload_data = {
        "project": project,
        "profile": _build_profile_payload(profile),
    }

    prompt = (
        "You are a project planner. "
        "Return a JSON array of phases for the project. "
        "Each phase must include: title, description, tasks (array of 4-6 short task strings). "
        "Return only valid JSON, no extra text.\n\n"
        f"Context: {json.dumps(payload_data)}"
    )

    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": "You only respond with JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": request.build_absolute_uri("/"),
        "X-Title": "RecoMagic",
    }

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return []

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError):
        return []

    if not isinstance(parsed, list):
        return []

    normalized = []
    task_id = 1
    for phase in parsed:
        if not isinstance(phase, dict):
            continue
        tasks_raw = phase.get("tasks", [])
        if not isinstance(tasks_raw, list):
            tasks_raw = []
        tasks = []
        for task_text in tasks_raw:
            tasks.append({"id": task_id, "description": str(task_text)})
            task_id += 1
        normalized.append(
            {
                "title": phase.get("title", "Phase"),
                "description": phase.get("description", ""),
                "tasks": tasks,
            }
        )
    return normalized


@login_required
def recommendations_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    recommendations = []
    ai_generated = False

    if profile:
        def normalize(value):
            return str(value or "").strip().lower()

        def split_tags(value):
            return {tag.strip().lower() for tag in str(value or "").split(",") if tag.strip()}

        field = normalize(profile.field)
        role = normalize(profile.target_role)
        goal = normalize(profile.learning_goal)
        tech = normalize(profile.tech_preference)
        skill = normalize(profile.skill_level)
        interests = split_tags(profile.interest_tags)

        candidates = [
            {
                "title": "AI Resume Matcher",
                "category": "AI Projects",
                "difficulty": "intermediate",
                "summary": "Match resumes to roles using embeddings and ranking.",
                "stack": ["python", "nlp", "vector search"],
                "fields": ["ai", "data science"],
                "roles": ["ml engineer", "data scientist"],
                "goals": ["portfolio", "skill improvement"],
                "interests": ["hr", "productivity"],
            },
            {
                "title": "E-commerce Forecasting",
                "category": "Data Science Projects",
                "difficulty": "intermediate",
                "summary": "Forecast demand using time-series signals and promos.",
                "stack": ["python", "pandas", "forecasting"],
                "fields": ["data science", "data analytics"],
                "roles": ["data analyst", "data scientist"],
                "goals": ["portfolio", "internship"],
                "interests": ["e-commerce", "retail"],
            },
            {
                "title": "Full Stack Event Booking",
                "category": "Web Development Projects",
                "difficulty": "intermediate",
                "summary": "Build a booking platform with payments and admin tools.",
                "stack": ["django", "postgresql", "payments"],
                "fields": ["web development"],
                "roles": ["full stack", "backend developer"],
                "goals": ["portfolio", "job"],
                "interests": ["events", "business"],
            },
            {
                "title": "Mobile Habit Coach",
                "category": "Mobile Projects",
                "difficulty": "beginner",
                "summary": "Create habits, streaks, and reminders on mobile.",
                "stack": ["flutter", "mobile", "notifications"],
                "fields": ["mobile development"],
                "roles": ["mobile developer"],
                "goals": ["skill improvement", "portfolio"],
                "interests": ["health", "productivity"],
            },
            {
                "title": "Cybersecurity Phishing Detector",
                "category": "Cybersecurity Projects",
                "difficulty": "intermediate",
                "summary": "Detect malicious URLs using ML features and heuristics.",
                "stack": ["python", "security", "ml"],
                "fields": ["cybersecurity", "ai"],
                "roles": ["security analyst"],
                "goals": ["portfolio", "skill improvement"],
                "interests": ["security"],
            },
            {
                "title": "Cloud Cost Optimizer",
                "category": "Cloud & DevOps Projects",
                "difficulty": "advanced",
                "summary": "Track spend and alert on unused cloud resources.",
                "stack": ["aws", "finops", "dashboards"],
                "fields": ["cloud", "devops"],
                "roles": ["devops", "cloud engineer"],
                "goals": ["job", "portfolio"],
                "interests": ["cloud", "finance"],
            },
            {
                "title": "Healthcare Scheduler",
                "category": "Web Development Projects",
                "difficulty": "intermediate",
                "summary": "Scheduling and reminders for clinics and patients.",
                "stack": ["django", "email", "calendar"],
                "fields": ["web development"],
                "roles": ["backend developer"],
                "goals": ["portfolio"],
                "interests": ["health"],
            },
            {
                "title": "Student Study Planner",
                "category": "EdTech Projects",
                "difficulty": "beginner",
                "summary": "Plan study sprints and track progress.",
                "stack": ["react", "ui", "analytics"],
                "fields": ["web development"],
                "roles": ["frontend developer"],
                "goals": ["portfolio", "internship"],
                "interests": ["education"],
            },
        ]

        def score(candidate):
            points = 0
            if field and field in candidate["fields"]:
                points += 3
            if role and role in candidate["roles"]:
                points += 2
            if goal and goal in candidate["goals"]:
                points += 2
            if tech and tech in candidate["stack"]:
                points += 2
            if interests and interests.intersection(set(candidate["interests"])):
                points += 2
            if skill and skill == candidate["difficulty"]:
                points += 1
            return points

        ranked = sorted(candidates, key=lambda item: (score(item), item["title"]), reverse=True)
        recommendations = ranked[:6]

        ai_recs = _fetch_ai_recommendations(profile, request)
        if ai_recs:
            recommendations = ai_recs
            ai_generated = True

        request.session["recommendations"] = recommendations

    return render(
        request,
        "users/recommendations.html",
        {"profile": profile, "recommendations": recommendations, "ai_generated": ai_generated},
    )


@login_required
@login_required
def start_recommendation_view(request, index):
    recommendations = request.session.get("recommendations", [])
    if not recommendations or index < 0 or index >= len(recommendations):
        return redirect("recommendations")

    project = recommendations[index]
    profile = UserProfile.objects.filter(user=request.user).first()
    project_id = f"rec-{index}"
    my_projects = request.session.get("my_projects", {})
    if project_id not in my_projects:
        my_projects[project_id] = {
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
        phases = _fetch_ai_phases(profile, project, request) if profile else []
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
            tasks.append({"id": task_id, "description": task.get("description"), "done": is_done})
        rendered_phases.append(
            {
                "title": phase.get("title"),
                "description": phase.get("description"),
                "tasks": tasks,
            }
        )

    progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    ai_error = not rendered_phases

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
        },
    )


@login_required
def my_projects_view(request):
    my_projects = request.session.get("my_projects", {})
    items = []

    for project_id, project in my_projects.items():
        phases = request.session.get(f"phases_{project_id}", [])
        completed = set(request.session.get(f"progress_{project_id}", []))
        total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)
        completed_tasks = sum(1 for phase in phases for task in phase.get("tasks", []) if task.get("id") in completed)
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
        items.append(
            {
                "id": project_id,
                "index": project.get("index"),
                "title": project.get("title"),
                "category": project.get("category"),
                "difficulty": project.get("difficulty"),
                "summary": project.get("summary"),
                "progress_pct": progress_pct,
                "completed_tasks": completed_tasks,
                "total_tasks": total_tasks,
            }
        )

    return render(request, "users/my_projects.html", {"projects": items})


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile_edit")
    else:
        form = SignUpForm()

    return render(request, "users/signup.html", {"form": form})


@login_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    return render(request, "users/profile_view.html", {"profile": profile})


@login_required
def profile_create_or_update(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect("profile_view")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "users/profile_form.html", {"form": form})