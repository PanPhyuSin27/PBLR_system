from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Plan, PremiumRequest


class CancelPremiumRequestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", email="tester@example.com", password="secret123")
        self.plan = Plan.objects.create(name="Pro Monthly", price=7000, description="Monthly plan")

    def test_pending_request_can_be_cancelled(self):
        PremiumRequest.objects.create(user=self.user, plan=self.plan, status="pending", note="Please review")

        self.client.force_login(self.user)
        response = self.client.post(reverse("cancel_premium_request"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('home')}#plans")
        self.assertFalse(PremiumRequest.objects.filter(user=self.user, status="pending").exists())
