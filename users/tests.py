from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DailyRecommendationUsage, Plan, PremiumRequest, Project, Subscription, UserProfile


class CancelPremiumRequestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", email="tester@example.com", password="secret123")
        self.plan, _ = Plan.objects.get_or_create(
            name="Pro Monthly",
            defaults={"price": 7000, "description": "Monthly plan"},
        )

    def test_pending_request_can_be_cancelled(self):
        PremiumRequest.objects.create(user=self.user, plan=self.plan, status="pending", note="Please review")

        self.client.force_login(self.user)
        response = self.client.post(reverse("cancel_premium_request"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('home')}#plans")
        self.assertFalse(PremiumRequest.objects.filter(user=self.user, status="pending").exists())


class RecommendationUsageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="explorer", email="explorer@example.com", password="secret123")
        UserProfile.objects.create(
            user=self.user,
            field="Data Science",
            target_role="Data Analyst",
            skill_level="beginner",
            tech_preference="Python, SQL",
            learning_goal="Build dashboards",
            interest_tags="analytics, dashboards",
        )
        for title in [
            "SQL Sales Dashboard",
            "Python KPI Dashboard",
            "Marketing Analytics Board",
            "Finance Metrics Console",
        ]:
            Project.objects.create(
                title=title,
                description="Build an interactive dashboard for regional sales trends.",
                field="Data Science",
                target_role="Data Analyst",
                skill_level="beginner",
                required_plan="explorer",
                tech_preference="Python, SQL",
                learning_goal="Build dashboards",
                interest_tags="analytics, dashboards",
            )
        Project.objects.create(
            title="Python Portfolio Site",
            description="Build a portfolio using familiar tools.",
            field="Web Development",
            target_role="Frontend Developer",
            skill_level="beginner",
            required_plan="explorer",
            tech_preference="Python, SQL",
            learning_goal="Build dashboards",
            interest_tags="analytics, dashboards",
        )
        for title in ["Statistics Notebook", "Survey Insight Report"]:
            Project.objects.create(
                title=title,
                description="Practice data science fundamentals with a different toolset.",
                field="Data Science",
                target_role="Data Analyst",
                skill_level="beginner",
                required_plan="explorer",
                tech_preference="R, Excel",
                learning_goal="Practice analysis",
                interest_tags="statistics, reporting",
            )

    def test_refresh_keeps_current_recommendations_and_regenerate_replaces_them(self):
        self.client.force_login(self.user)

        first_response = self.client.get(reverse("recommendations"))
        first_ids = [project["id"] for project in self.client.session["recommendations"]]
        second_response = self.client.get(reverse("recommendations"))
        second_ids = [project["id"] for project in self.client.session["recommendations"]]
        regenerate_response = self.client.post(reverse("recommendations"))
        regenerated_ids = [project["id"] for project in self.client.session["recommendations"]]

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertRedirects(regenerate_response, reverse("recommendations"))
        usage = DailyRecommendationUsage.objects.get(user=self.user, usage_date=timezone.localdate())
        self.assertEqual(usage.count, 2)
        self.assertTrue(first_ids)
        self.assertTrue(second_ids)
        self.assertEqual(first_ids, second_ids)
        self.assertNotEqual(first_ids, regenerated_ids)
        self.assertTrue(set(regenerated_ids) - set(first_ids))
        self.assertTrue(all(project["category"] == "Data Science" for project in self.client.session["recommendations"]))

    def test_premium_refresh_keeps_current_recommendations_and_regenerate_replaces_them_without_usage(self):
        premium_user = get_user_model().objects.create_user(
            username="premium",
            email="premium@example.com",
            password="secret123",
        )
        UserProfile.objects.create(
            user=premium_user,
            field="Data Science",
            target_role="Data Analyst",
            skill_level="beginner",
            tech_preference="Python, SQL",
            learning_goal="Build dashboards",
            interest_tags="analytics, dashboards",
        )
        plan, _ = Plan.objects.get_or_create(
            name="Pro Monthly",
            defaults={"price": 7000, "description": "Monthly plan"},
        )
        Subscription.objects.create(
            user=premium_user,
            plan=plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            is_active=True,
        )
        for index in range(1, 9):
            Project.objects.create(
                title=f"Premium Data Project {index}",
                description="Build a premium analytics project.",
                field="Data Science",
                target_role="Data Analyst",
                skill_level="beginner",
                required_plan="pro_monthly" if index > 4 else "explorer",
                tech_preference="Python, SQL",
                learning_goal="Build dashboards",
                interest_tags="analytics, dashboards",
            )

        self.client.force_login(premium_user)

        first_response = self.client.get(reverse("recommendations"))
        first_ids = [project["id"] for project in self.client.session["recommendations"]]
        refresh_response = self.client.get(reverse("recommendations"))
        refresh_ids = [project["id"] for project in self.client.session["recommendations"]]
        regenerate_response = self.client.post(reverse("recommendations"))
        regenerated_ids = [project["id"] for project in self.client.session["recommendations"]]

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(refresh_response.status_code, 200)
        self.assertRedirects(regenerate_response, reverse("recommendations"))
        self.assertEqual(first_ids, refresh_ids)
        self.assertNotEqual(first_ids, regenerated_ids)
        self.assertTrue(set(regenerated_ids) - set(first_ids))
        self.assertFalse(DailyRecommendationUsage.objects.filter(user=premium_user).exists())
        self.assertTrue(all(project["category"] == "Data Science" for project in self.client.session["recommendations"]))

    def test_my_projects_regenerate_posts_to_recommendations(self):
        self.client.force_login(self.user)
        self.client.get(reverse("recommendations"))
        recommendation = self.client.session["recommendations"][0]
        session = self.client.session
        session["my_projects"] = {
            "rec-0": {
                "source": "recommendation",
                "index": 0,
                "title": recommendation["title"],
                "category": recommendation["category"],
                "difficulty": recommendation["difficulty"],
                "summary": recommendation["summary"],
            }
        }
        session.save()

        response = self.client.get(reverse("my_projects"))

        self.assertContains(response, f'action="{reverse("recommendations")}"')
        self.assertNotContains(response, f'{reverse("start_recommendation", args=[0])}?regen=1')
