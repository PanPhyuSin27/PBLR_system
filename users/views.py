import json
import os
import urllib.error
import urllib.request

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
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


def _normalize_learning_style(value):
    if not value:
        return ""
    raw = str(value).strip().lower()
    mapping = {
        "step-by-step": "step_by_step",
        "step by step": "step_by_step",
        "step_by_step": "step_by_step",
        "hands-on": "hands_on",
        "hands on": "hands_on",
        "hands_on": "hands_on",
        "visual + examples": "visual_examples",
        "visual examples": "visual_examples",
        "visual_examples": "visual_examples",
        "short lessons + practice": "short_lessons",
        "short lessons": "short_lessons",
        "short_lessons": "short_lessons",
        "guided checklist": "guided_checklist",
        "guided_checklist": "guided_checklist",
    }
    return mapping.get(raw, raw)


SHOWCASE_PROJECTS = {
    "resume-matcher": {
        "title": "Resume Matcher",
        "category": "AI Projects",
        "difficulty": "intermediate",
        "summary": "Score resumes against job descriptions using embeddings.",
        "stack": ["NLP", "Vector Search", "Python"],
    },
    "customer-support-copilot": {
        "title": "Customer Support Copilot",
        "category": "AI Projects",
        "difficulty": "intermediate",
        "summary": "Summarize tickets and suggest responses with LLMs.",
        "stack": ["LLM", "RAG", "Workflow"],
    },
    "visual-quality-inspector": {
        "title": "Visual Quality Inspector",
        "category": "AI Projects",
        "difficulty": "intermediate",
        "summary": "Detect product defects using image classification.",
        "stack": ["Computer Vision", "CNN", "MLOps"],
    },
    "smart-meeting-notes": {
        "title": "Smart Meeting Notes",
        "category": "AI Projects",
        "difficulty": "intermediate",
        "summary": "Transcribe and extract action items automatically.",
        "stack": ["ASR", "Summarization", "Productivity"],
    },
    "sales-insight-dashboard": {
        "title": "Sales Insight Dashboard",
        "category": "Data Science Projects",
        "difficulty": "intermediate",
        "summary": "Analyze revenue, cohorts, and growth trends with visuals.",
        "stack": ["Pandas", "BI", "Metrics"],
    },
    "customer-churn-model": {
        "title": "Customer Churn Model",
        "category": "Data Science Projects",
        "difficulty": "intermediate",
        "summary": "Predict churn risk and highlight retention levers.",
        "stack": ["Classification", "Feature Eng", "Python"],
    },
    "price-elasticity-study": {
        "title": "Price Elasticity Study",
        "category": "Data Science Projects",
        "difficulty": "intermediate",
        "summary": "Measure demand sensitivity using regression models.",
        "stack": ["Regression", "Econometrics", "Forecasting"],
    },
    "ab-test-analyzer": {
        "title": "A/B Test Analyzer",
        "category": "Data Science Projects",
        "difficulty": "intermediate",
        "summary": "Automate experiment results and significance checks.",
        "stack": ["Stats", "Experimentation", "Reporting"],
    },
    "job-board-api": {
        "title": "Job Board API",
        "category": "Web Development Projects",
        "difficulty": "intermediate",
        "summary": "Create a REST API with auth, filtering, and role-based access.",
        "stack": ["Django", "REST", "JWT"],
    },
    "portfolio-builder": {
        "title": "Portfolio Builder",
        "category": "Web Development Projects",
        "difficulty": "beginner",
        "summary": "Design a responsive site builder with templates and previews.",
        "stack": ["React", "UI", "Responsive"],
    },
    "freelance-crm": {
        "title": "Freelance CRM",
        "category": "Web Development Projects",
        "difficulty": "intermediate",
        "summary": "Manage clients, invoices, and email workflows.",
        "stack": ["PostgreSQL", "Email", "SaaS"],
    },
    "event-booking-platform": {
        "title": "Event Booking Platform",
        "category": "Web Development Projects",
        "difficulty": "intermediate",
        "summary": "Handle listings, ticketing, and secure checkout flows.",
        "stack": ["Stripe", "Payments", "UX"],
    },
    "habit-coach-app": {
        "title": "Habit Coach App",
        "category": "Mobile Projects",
        "difficulty": "beginner",
        "summary": "Build streaks, reminders, and progress charts on mobile.",
        "stack": ["Flutter", "Charts", "Notifications"],
    },
    "campus-navigator": {
        "title": "Campus Navigator",
        "category": "Mobile Projects",
        "difficulty": "intermediate",
        "summary": "Interactive maps with routing and accessibility layers.",
        "stack": ["Maps", "Geolocation", "UX"],
    },
    "meal-planner": {
        "title": "Meal Planner",
        "category": "Mobile Projects",
        "difficulty": "beginner",
        "summary": "Plan weekly meals, track macros, and auto-generate lists.",
        "stack": ["Health", "Offline", "Sync"],
    },
    "expense-tracker": {
        "title": "Expense Tracker",
        "category": "Mobile Projects",
        "difficulty": "beginner",
        "summary": "Scan receipts and categorize spending on-device.",
        "stack": ["OCR", "FinTech", "Insights"],
    },
    "serverless-image-api": {
        "title": "Serverless Image API",
        "category": "Cloud & DevOps Projects",
        "difficulty": "intermediate",
        "summary": "Resize and optimize images with on-demand functions.",
        "stack": ["AWS", "Lambda", "S3"],
    },
    "cicd-control-center": {
        "title": "CI/CD Control Center",
        "category": "Cloud & DevOps Projects",
        "difficulty": "intermediate",
        "summary": "Monitor pipelines, deployments, and alerts.",
        "stack": ["Docker", "CI", "Observability"],
    },
    "infra-cost-optimizer": {
        "title": "Infra Cost Optimizer",
        "category": "Cloud & DevOps Projects",
        "difficulty": "advanced",
        "summary": "Track cloud spend and flag underused services.",
        "stack": ["FinOps", "Dashboards", "Alerts"],
    },
    "observability-starter-kit": {
        "title": "Observability Starter Kit",
        "category": "Cloud & DevOps Projects",
        "difficulty": "intermediate",
        "summary": "Set up logs, traces, and SLO dashboards quickly.",
        "stack": ["OpenTelemetry", "SLO", "Grafana"],
    },
    "phishing-detection": {
        "title": "Phishing Detection",
        "category": "Cybersecurity Projects",
        "difficulty": "intermediate",
        "summary": "Detect suspicious URLs with ML features and heuristics.",
        "stack": ["Security", "ML", "Python"],
    },
    "password-health-scanner": {
        "title": "Password Health Scanner",
        "category": "Cybersecurity Projects",
        "difficulty": "beginner",
        "summary": "Audit password strength and policy compliance.",
        "stack": ["Policies", "Risk", "CLI"],
    },
    "threat-log-explorer": {
        "title": "Threat Log Explorer",
        "category": "Cybersecurity Projects",
        "difficulty": "intermediate",
        "summary": "Search security logs and flag anomalies.",
        "stack": ["SIEM", "Detection", "Analytics"],
    },
    "secure-file-vault": {
        "title": "Secure File Vault",
        "category": "Cybersecurity Projects",
        "difficulty": "intermediate",
        "summary": "Encrypt files with key management and access auditing.",
        "stack": ["Encryption", "IAM", "Compliance"],
    },
}


def _get_showcase_project(slug):
    project = SHOWCASE_PROJECTS.get(slug)
    if project:
        return project.copy()
    title = str(slug or "showcase project").replace("-", " ").title()
    return {
        "title": title,
        "category": "Showcase Projects",
        "difficulty": "intermediate",
        "summary": "Showcase project from the library.",
        "stack": [],
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
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        
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


def _fetch_ai_phases(profile, project, request, learning_style=None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        request.session["ai_error_detail"] = "Missing OPENROUTER_API_KEY in .env"
        return []

    payload_data = {
        "project": project,
        "profile": _build_profile_payload(profile),
    }

    if learning_style:
        payload_data["learning_style"] = learning_style

    if learning_style:
        prompt = (
            "You are a project planner and learning coach. "
            "Return a JSON array of phases for the project. "
            "Each phase must include: title, description, resources (array of {title, url}), and tasks. "
            "Each task must include: description, steps (array of 3-5 short steps), "
            "learn (1-2 sentence micro-lesson), and key_terms (array of 3-5 terms). "
            "Return only valid JSON, no extra text.\n\n"
            f"Context: {json.dumps(payload_data)}"
        )
    else:
        prompt = (
            "You are a project planner. "
            "Return a JSON array of phases for the project. "
            "Each phase must include: title, description, tasks (array of 4-6 short task strings). "
            "Return only valid JSON, no extra text.\n\n"
            f"Context: {json.dumps(payload_data)}"
        )

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
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
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""
        request.session["ai_error_detail"] = f"OpenRouter HTTP {exc.code}: {error_body[:200]}"
        return []
    except urllib.error.URLError as exc:
        request.session["ai_error_detail"] = f"OpenRouter connection error: {exc.reason}"
        return []
    except json.JSONDecodeError:
        request.session["ai_error_detail"] = "OpenRouter response was not valid JSON"
        return []

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError):
        request.session["ai_error_detail"] = "OpenRouter response format was unexpected"
        return []

    if not isinstance(parsed, list):
        return []

    normalized = []
    task_id = 1
    for phase in parsed:
        if not isinstance(phase, dict):
            continue
        resources = []
        resources_raw = phase.get("resources", [])
        if isinstance(resources_raw, list):
            for resource in resources_raw:
                if isinstance(resource, dict) and resource.get("url"):
                    resources.append(
                        {
                            "title": str(resource.get("title") or resource.get("url")),
                            "url": str(resource.get("url")),
                        }
                    )
        tasks_raw = phase.get("tasks", [])
        if not isinstance(tasks_raw, list):
            tasks_raw = []
        tasks = []
        for task_item in tasks_raw:
            if isinstance(task_item, dict):
                description = task_item.get("description") or task_item.get("title") or task_item.get("task")
                steps = task_item.get("steps", [])
                key_terms = task_item.get("key_terms", [])
                if not isinstance(steps, list):
                    steps = []
                if not isinstance(key_terms, list):
                    key_terms = []
                tasks.append(
                    {
                        "id": task_id,
                        "description": str(description or "Task"),
                        "steps": [str(step) for step in steps],
                        "learn": str(task_item.get("learn", "")),
                        "key_terms": [str(term) for term in key_terms],
                    }
                )
            else:
                tasks.append({"id": task_id, "description": str(task_item), "steps": [], "learn": "", "key_terms": []})
            task_id += 1
        normalized.append(
            {
                "title": phase.get("title", "Phase"),
                "description": phase.get("description", ""),
                "resources": resources,
                "tasks": tasks,
            }
        )
    return normalized


def _phases_have_guidance(phases):
    for phase in phases:
        if phase.get("resources"):
            return True
        for task in phase.get("tasks", []):
            if task.get("steps") or task.get("learn") or task.get("key_terms"):
                return True
    return False


def _default_guidance_for_task(description, learning_style):
    task_text = str(description or "this task").strip()
    learning_style = _normalize_learning_style(learning_style)
    style_map = {
        "step_by_step": [
            "Define the goal and acceptance criteria",
            "List the inputs, outputs, and constraints",
            "Implement in small, ordered steps",
            "Verify against the criteria",
            "Summarize what changed",
        ],
        "hands_on": [
            "Build a quick prototype",
            "Run it and observe behavior",
            "Tweak parameters and compare results",
            "Harden the final version",
        ],
        "visual_examples": [
            "Sketch the flow or UI",
            "Collect 1-2 reference examples",
            "Replicate the core pattern",
            "Adapt it to your scenario",
        ],
        "short_lessons": [
            "Read a 5-10 min primer",
            "Try a micro exercise",
            "Apply the concept to the task",
            "Review and refine",
        ],
        "guided_checklist": [
            "Confirm prerequisites",
            "Complete checklist items",
            "Validate expected output",
            "Mark the task done",
        ],
    }

    steps = style_map.get(learning_style, style_map["step_by_step"]).copy()

    learn_templates = {
        "step_by_step": f"Focus on clear criteria and ordered execution for: {task_text}.",
        "hands_on": f"Learn by building and iterating directly on: {task_text}.",
        "visual_examples": f"Use examples and visual flow to guide: {task_text}.",
        "short_lessons": f"Apply a short lesson, then practice on: {task_text}.",
        "guided_checklist": f"Follow a checklist to complete: {task_text}.",
    }
    learn = learn_templates.get(learning_style, learn_templates["step_by_step"]).strip()

    stopwords = {
        "the",
        "and",
        "with",
        "this",
        "that",
        "from",
        "your",
        "into",
        "for",
        "then",
        "when",
        "what",
        "how",
        "build",
        "make",
        "create",
        "setup",
    }
    words = [
        word.strip(".,:;!?")
        for word in str(description or "").lower().split()
        if len(word.strip(".,:;!?")) > 3
    ]
    key_terms = []
    for word in words:
        if word in stopwords:
            continue
        if word not in key_terms:
            key_terms.append(word)
        if len(key_terms) >= 5:
            break

    return steps, learn, key_terms


def _ensure_guidance(phases, learning_style):
    if not learning_style:
        return phases
    for phase in phases:
        for task in phase.get("tasks", []):
            steps, learn, key_terms = _default_guidance_for_task(task.get("description"), learning_style)
            if not task.get("steps"):
                task["steps"] = steps
            if not task.get("learn"):
                task["learn"] = learn
            if not task.get("key_terms"):
                task["key_terms"] = key_terms
    return phases


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
    learning_style = _normalize_learning_style(profile.learning_style) if profile else ""
    show_guidance = bool(learning_style)
    project_id = f"rec-{index}"
    my_projects = request.session.get("my_projects", {})
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
        phases = _fetch_ai_phases(profile, project, request, learning_style) if profile else []
        if phases:
            request.session[phases_key] = phases
        else:
            phases = []
    else:
        phases = request.session.get(phases_key, [])

    if show_guidance and phases and not _phases_have_guidance(phases):
        request.session.pop(progress_key, None)
        guided_phases = _fetch_ai_phases(profile, project, request, learning_style) if profile else []
        if guided_phases:
            phases = guided_phases
            request.session[phases_key] = phases

    if show_guidance and phases:
        phases = _ensure_guidance(phases, learning_style)
        request.session[phases_key] = phases

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
    ai_error = not rendered_phases
    ai_error_detail = request.session.pop("ai_error_detail", "")

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
            "show_guidance": show_guidance,
        },
    )


@login_required
def start_showcase_view(request, slug):
    project = _get_showcase_project(slug)
    profile = UserProfile.objects.filter(user=request.user).first()
    learning_style = _normalize_learning_style(profile.learning_style) if profile else ""
    show_guidance = bool(learning_style)

    project_id = f"showcase-{slug}"
    my_projects = request.session.get("my_projects", {})
    if project_id not in my_projects:
        my_projects[project_id] = {
            "source": "showcase",
            "slug": slug,
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
        phases = _fetch_ai_phases(profile, project, request, learning_style) if profile else []
        if phases:
            request.session[phases_key] = phases
        else:
            phases = []
    else:
        phases = request.session.get(phases_key, [])

    if show_guidance and phases:
        phases = _ensure_guidance(phases, learning_style)
        request.session[phases_key] = phases

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
    ai_error = not rendered_phases
    ai_error_detail = request.session.pop("ai_error_detail", "")

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
            "show_guidance": show_guidance,
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
        if project.get("source") == "showcase":
            start_url = reverse("start_showcase", args=[project.get("slug")])
        else:
            start_url = reverse("start_recommendation", args=[project.get("index")])
        items.append(
            {
                "id": project_id,
                "index": project.get("index"),
                "source": project.get("source", "recommendation"),
                "start_url": start_url,
                "regen_url": f"{start_url}?regen=1",
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
            backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user, backend=backend)
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