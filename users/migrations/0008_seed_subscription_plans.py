from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("users", "Plan")

    plans = [
        {
            "name": "Explorer Plan (Free)",
            "price": "0.00",
            "description": (
                "The Explorer Plan is designed for learners who want to explore project-based learning "
                "with basic personalized recommendations. It provides limited daily suggestions and "
                "essential features to help users begin their structured learning journey."
            ),
            "features": "\n".join(
                [
                    "• Up to 3 personalized project recommendations per day",
                    "• Basic project filtering (category and difficulty)",
                    "• Save up to 5 projects",
                    "• Access to standard learning roadmap",
                    "• Limited personalization depth",
                ]
            ),
        },
        {
            "name": "Pro Monthly",
            "price": "7000.00",
            "description": (
                "The Pro Monthly Plan unlocks advanced AI-powered personalized project recommendations, "
                "skill-gap analysis, and unlimited access to curated learning roadmaps. Ideal for serious "
                "learners who want continuous growth and industry-aligned project guidance."
            ),
            "features": "\n".join(
                [
                    "• Unlimited personalized project recommendations",
                    "• AI-powered skill gap analysis",
                    "• Resume-based project suggestions",
                    "• Industry trend-aligned recommendations",
                    "• Unlimited saved projects",
                    "• Downloadable PDF project roadmap",
                    "• Detailed tech stack explanation",
                    "• Priority access to new projects",
                ]
            ),
        },
        {
            "name": "Pro Yearly",
            "price": "70000.00",
            "description": (
                "The Pro Yearly Plan offers all Premium features with long-term access at a discounted rate. "
                "Designed for committed learners, it provides uninterrupted AI-driven recommendations and "
                "structured career-focused project development throughout the year."
            ),
            "features": "\n".join(
                [
                    "• All Pro Monthly features included",
                    "• 12 months full access at discounted price",
                    "• Long-term learning progress tracking",
                    "• Early access to new datasets and templates",
                    "• Priority feature updates",
                ]
            ),
        },
    ]

    for item in plans:
        Plan.objects.update_or_create(
            name=item["name"],
            defaults={
                "price": item["price"],
                "description": item["description"],
                "features": item["features"],
            },
        )


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("users", "Plan")
    Plan.objects.filter(name__in=["Explorer Plan (Free)", "Pro Monthly", "Pro Yearly"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_merge_premium_request"),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
