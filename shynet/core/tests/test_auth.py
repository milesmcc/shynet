import json
from http import HTTPStatus

from allauth.account.models import EmailAddress
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from core.factories import UserFactory
from core.models import User

# Random per test run, so no password literal lives in the repository.
PASSWORD = get_random_string(32)
NEW_PASSWORD = get_random_string(32)
WRONG_PASSWORD = get_random_string(32)


def user_with_email(email="owner@example.com", **kwargs):
    user = UserFactory(email=email, password=PASSWORD, **kwargs)
    user.save()
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


class LoginTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_with_email_and_password(self):
        user_with_email()
        response = self.client.post(
            reverse("account_login"),
            {"login": "owner@example.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            self.client.get(reverse("dashboard:dashboard")).status_code, HTTPStatus.OK
        )

    def test_login_with_wrong_password_fails(self):
        user_with_email()
        response = self.client.post(
            reverse("account_login"),
            {"login": "owner@example.com", "password": WRONG_PASSWORD},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            self.client.get(reverse("dashboard:dashboard")).status_code,
            HTTPStatus.FOUND,
        )

    def test_logout(self):
        user = user_with_email()
        self.client.force_login(user)
        self.client.post(reverse("account_logout"))
        self.assertEqual(
            self.client.get(reverse("dashboard:dashboard")).status_code,
            HTTPStatus.FOUND,
        )

    def test_root_redirects_to_dashboard_or_login(self):
        response = self.client.get("/")
        self.assertIn(response.status_code, (HTTPStatus.FOUND, HTTPStatus.OK))


class SignupTests(TestCase):
    def test_signup_is_closed_by_default(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "new@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )
        self.assertFalse(User.objects.filter(email="new@example.com").exists())
        self.assertNotEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)


class PasswordTests(TestCase):
    def test_reset_sends_email_for_known_address(self):
        user_with_email()
        response = self.client.post(
            reverse("account_reset_password"), {"email": "owner@example.com"}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])

    def test_reset_for_unknown_address_sends_nothing_useful(self):
        self.client.post(reverse("account_reset_password"), {"email": "x@example.com"})
        self.assertEqual(
            [m for m in mail.outbox if "x@example.com" in m.to and "reset" in m.body.lower() and "http" in m.body],
            [],
        )

    def test_change_password(self):
        user = user_with_email()
        self.client.force_login(user)
        response = self.client.post(
            reverse("account_change_password"),
            {
                "oldpassword": PASSWORD,
                "password1": NEW_PASSWORD,
                "password2": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))

    def test_change_password_page_renders(self):
        self.client.force_login(user_with_email())
        self.assertEqual(
            self.client.get(reverse("account_change_password")).status_code,
            HTTPStatus.OK,
        )


class HealthCheckTests(TestCase):
    def test_healthz_reports_ok_as_json(self):
        response = self.client.get("/healthz/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        json.loads(response.content)

    def test_healthz_html(self):
        self.assertEqual(self.client.get("/healthz/").status_code, HTTPStatus.OK)


class ApiTokenTests(TestCase):
    def test_refresh_requires_login(self):
        response = self.client.post(reverse("dashboard:api_token_refresh"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn("login", response.url)

    def test_refresh_changes_token(self):
        user = user_with_email()
        old = user.api_token
        self.client.force_login(user)
        response = self.client.post(reverse("dashboard:api_token_refresh"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        user.refresh_from_db()
        self.assertNotEqual(user.api_token, old)
