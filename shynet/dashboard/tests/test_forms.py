from allauth.account.models import EmailAddress
from django.test import TestCase

from core.factories import UserFactory
from dashboard.forms import ServiceForm

BASE = {
    "name": "Site",
    "link": "https://site.example",
    "respect_dnt": "True",
    "collect_ips": "True",
    "ignored_ips": "",
    "ignore_robots": "False",
    "hide_referrer_regex": "",
    "origins": "*",
    "collaborators": "",
    "script_inject": "",
}


def register(email):
    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


class ServiceFormTests(TestCase):
    def test_valid_minimal_form(self):
        self.assertTrue(ServiceForm(BASE).is_valid())

    def test_collaborators_are_resolved_case_insensitively(self):
        user = register("Collab@Example.com")
        form = ServiceForm(dict(BASE, collaborators=" collab@example.com , "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["collaborators"], [user])

    def test_unknown_collaborator_is_rejected(self):
        form = ServiceForm(dict(BASE, collaborators="ghost@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("not registered", str(form.errors["collaborators"]))

    def test_duplicate_collaborator_is_rejected(self):
        register("a@example.com")
        form = ServiceForm(dict(BASE, collaborators="a@example.com, A@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("same user", str(form.errors["collaborators"]))

    def test_invalid_network_and_regex_are_rejected(self):
        form = ServiceForm(dict(BASE, ignored_ips="bad", hide_referrer_regex="("))
        self.assertFalse(form.is_valid())
        self.assertIn("ignored_ips", form.errors)
        self.assertIn("hide_referrer_regex", form.errors)

    def test_collect_ips_can_be_unchecked(self):
        form = ServiceForm({k: v for k, v in BASE.items() if k != "collect_ips"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["collect_ips"])
