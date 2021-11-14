from django.test import TestCase, RequestFactory
from django.conf import settings
from django.urls import reverse
from core.factories import UserFactory

from dashboard.views import DashboardView


class QuestionModelTests(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = UserFactory()

    def tearDown(self):
        pass

    def tests_unauthenticated_dashboard_view(self):
        """
        GIVEN: Unauthenticated user
        WHEN: Accessing the dashboard view
        THEN: It's redirected to login page with NEXT url to dashboard
        """
        login_url = settings.LOGIN_URL
        response = self.client.get(reverse("dashboard:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, f"{login_url}?next={reverse('dashboard:dashboard')}"
        )

    def tests_authenticated_dashboard_view(self):
        """
        GIVEN: Authenticated user
        WHEN: Accessing the dashboard view
        THEN: It should respond with 200 and render the view
        """
        request = self.factory.get(reverse("dashboard:dashboard"))
        request.user = self.user

        # Use this syntax for class-based views.
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)
