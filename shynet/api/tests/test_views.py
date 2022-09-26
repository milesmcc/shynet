import json
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from api.views import DashboardApiView
from core.factories import UserFactory, ServiceFactory
from core.models import Service

User = get_user_model()


class TestDashboardApiView(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user: User = UserFactory()
        self.service_1: Service = ServiceFactory(owner=self.user)
        self.service_2: Service = ServiceFactory(owner=self.user)
        self.url = reverse("api:services")
        self.factory = RequestFactory()

    def test_get_with_unauthenticated_user(self):
        """
        GIVEN: An unauthenticated user
        WHEN: The user makes a GET request to the dashboard API view
        THEN: It should return 403
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_returns_400(self):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view with an invalid date format
        THEN: It should return 400
        """
        request = self.factory.get(self.url, {"startDate": "01/01/2000"})
        request.META["HTTP_AUTHORIZATION"] = f"Token {self.user.api_token}"

        response = DashboardApiView.as_view()(request)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid date format. Use YYYY-MM-DD.")

    def test_get_with_authenticated_user(self):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view
        THEN: It should return 200
        """
        request = self.factory.get(self.url)
        request.META["HTTP_AUTHORIZATION"] = f"Token {self.user.api_token}"

        response = DashboardApiView.as_view()(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = json.loads(response.content)
        self.assertEqual(len(data["services"]), 2)

    def test_get_with_service_uuid(self):
        """
        GIVEN: An authenticated user
        WHEN: The user makes a GET request to the dashboard API view with a service UUID
        THEN: It should return 200 and a single service
        """
        request = self.factory.get(self.url, {"uuid": str(self.service_1.uuid)})
        request.META["HTTP_AUTHORIZATION"] = f"Token {self.user.api_token}"

        response = DashboardApiView.as_view()(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        data = json.loads(response.content)
        self.assertEqual(len(data["services"]), 1)
        self.assertEqual(data["services"][0]["uuid"], str(self.service_1.uuid))
        self.assertEqual(data["services"][0]["name"], str(self.service_1.name))

