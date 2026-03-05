from django.db.models import Q

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


def recommend_projects_for_profile(profile, limit=6, user_plan_tier="explorer"):
    profile_field = _normalize(profile.field)
    profile_skill = _normalize(profile.skill_level)
    profile_tech = _normalize(profile.tech_preference)
    profile_goal = _normalize(profile.learning_goal)
    profile_tags = _split_tags(profile.interest_tags)

    if not profile_skill:
        return []

    user_rank = PLAN_RANK.get(user_plan_tier, 0)
    allowed_tiers = [tier for tier, rank in PLAN_RANK.items() if rank <= user_rank]

    tag_filter = None
    for tag in profile_tags:
        condition = Q(interest_tags__icontains=tag)
        tag_filter = condition if tag_filter is None else tag_filter | condition

    candidate_filter = None
    if profile_field:
        condition = Q(field__iexact=profile.field)
        candidate_filter = condition if candidate_filter is None else candidate_filter | condition
    if profile_tech:
        condition = Q(tech_preference__icontains=profile.tech_preference)
        candidate_filter = condition if candidate_filter is None else candidate_filter | condition
    if profile_goal:
        condition = Q(learning_goal__icontains=profile.learning_goal)
        candidate_filter = condition if candidate_filter is None else candidate_filter | condition
    if tag_filter is not None:
        candidate_filter = tag_filter if candidate_filter is None else candidate_filter | tag_filter

    projects_qs = Project.objects.filter(skill_level=profile.skill_level, required_plan__in=allowed_tiers)
    if candidate_filter is not None:
        projects_qs = projects_qs.filter(candidate_filter)

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

    scored.sort(key=lambda item: (-item[0], item[1].title.lower(), item[1].id))

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
        for score, project in scored[:limit]
    ]
