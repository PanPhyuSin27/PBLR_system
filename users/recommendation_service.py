import random

from .models import Project


PLAN_RANK = {
    "explorer": 0,
    "pro_monthly": 1,
    "pro_yearly": 2,
}


def _normalize(value):
    return str(value or "").strip().lower()


def _split_tags(value):
    return {tag.strip().lower() for tag in str(value or "").split(",") if tag.strip()}


def recommend_projects_for_profile(profile, limit=6, user_plan_tier="explorer", exclude_project_ids=None):
    profile_field = _normalize(profile.field)
    profile_skill = _normalize(profile.skill_level)
    profile_tech = _normalize(profile.tech_preference)
    profile_goal = _normalize(profile.learning_goal)
    profile_tags = _split_tags(profile.interest_tags)

    if not profile_skill:
        return []

    user_rank = PLAN_RANK.get(user_plan_tier, 0)
    allowed_tiers = [tier for tier, rank in PLAN_RANK.items() if rank <= user_rank]

    projects_qs = Project.objects.filter(skill_level=profile.skill_level, required_plan__in=allowed_tiers)
    if profile_field:
        projects_qs = projects_qs.filter(field__iexact=profile.field)

    scored = []
    for project in projects_qs:
        score = 0

        project_field = _normalize(project.field)
        project_tech = _normalize(project.tech_preference)
        project_goal = _normalize(project.learning_goal)
        project_tags = _split_tags(project.interest_tags)

        if profile_field and project_field == profile_field:
            score += 4

        score += 4

        if profile_tech and (profile_tech in project_tech or project_tech in profile_tech):
            score += 3

        if profile_goal and (profile_goal in project_goal or project_goal in profile_goal):
            score += 2

        overlap = profile_tags.intersection(project_tags)
        if overlap:
            score += len(overlap) * 2

        scored.append((score, project))

    excluded_ids = {int(project_id) for project_id in (exclude_project_ids or []) if project_id}
    random.shuffle(scored)
    fresh_scored = [item for item in scored if item[1].id not in excluded_ids]
    fallback_scored = [item for item in scored if item[1].id in excluded_ids]
    fresh_scored.sort(key=lambda item: -item[0])
    fallback_scored.sort(key=lambda item: -item[0])
    selected = (fresh_scored + fallback_scored)[:limit]

    return [
        {
            "id": project.id,
            "title": project.title,
            "category": project.field,
            "difficulty": project.skill_level,
            "summary": project.description,
            "required_plan": project.required_plan,
            "stack": [token.strip() for token in str(project.tech_preference).split(",") if token.strip()],
            "target_role": project.target_role,
            "learning_goal": project.learning_goal,
            "interest_tags": project.interest_tags,
            "relevance_score": score,
        }
        for score, project in selected
    ]
