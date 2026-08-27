from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DailyRecommendationUsage, Plan, PremiumRequest, Project, UserProfile


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

    def test_refresh_consumes_another_free_recommendation_and_avoids_previous_projects(self):
        self.client.force_login(self.user)

        first_response = self.client.get(reverse("recommendations"))
        first_ids = [project["id"] for project in self.client.session["recommendations"]]
        second_response = self.client.get(reverse("recommendations"))
        second_ids = [project["id"] for project in self.client.session["recommendations"]]

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        usage = DailyRecommendationUsage.objects.get(user=self.user, usage_date=timezone.localdate())
        self.assertEqual(usage.count, 2)
        self.assertTrue(first_ids)
        self.assertTrue(second_ids)
        self.assertNotEqual(first_ids, second_ids)
        self.assertTrue(set(second_ids) - set(first_ids))
        self.assertTrue(all(project["category"] == "Data Science" for project in self.client.session["recommendations"]))
