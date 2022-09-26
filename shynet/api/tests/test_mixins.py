from http import HTTPStatus

from django.test import TestCase, RequestFactory
from django.views import View

from api.mixins import ApiTokenRequiredMixin
from core.factories import UserFactory
from core.models import _default_api_token, Service


class TestApiTokenRequiredMixin(TestCase):
    class DummyView(ApiTokenRequiredMixin, View):
        model = Service
        template_name = "dashboard/pages/service.html"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.request = RequestFactory().get("/fake-path")

        # Setup request and view.
        self.factory = RequestFactory()
        self.view = self.DummyView()

    def test_get_user_by_token_without_authorization_token(self):
        """
        GIVEN: A request without Authorization header
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        user = self.view._get_user_by_token(self.request)

        self.assertEqual(user.is_anonymous, True)

    def test_get_user_by_token_with_invalid_authorization_token(self):
        """
        GIVEN: A request with invalid Authorization header
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        self.request.META["HTTP_AUTHORIZATION"] = "Bearer invalid-token"
        user = self.view._get_user_by_token(self.request)

        self.assertEqual(user.is_anonymous, True)

    def test_get_user_by_token_with_invalid_token(self):
        """
        GIVEN: A request with invalid token
        WHEN: get_user_by_token is called
        THEN: It should return AnonymousUser
        """
        self.request.META["HTTP_AUTHORIZATION"] = f"Token {_default_api_token()}"
        user = self.view._get_user_by_token(self.request)

        self.assertEqual(user.is_anonymous, True)

    def test_get_user_by_token_with_valid_token(self):
        """
        GIVEN: A request with valid token
        WHEN: get_user_by_token is called
        THEN: It should return the user
        """
        self.request.META["HTTP_AUTHORIZATION"] = f"Token {self.user.api_token}"
        user = self.view._get_user_by_token(self.request)

        self.assertEqual(user, self.user)

    def test_dispatch_with_unauthenticated_user(self):
        """
        GIVEN: A request with unauthenticated user
        WHEN: dispatch is called
        THEN: It should return 403
        """
        self.request.META["HTTP_AUTHORIZATION"] = f"Token {_default_api_token()}"
        response = self.view.dispatch(self.request)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
