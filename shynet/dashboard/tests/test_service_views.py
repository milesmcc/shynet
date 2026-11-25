from datetime import timedelta
from http import HTTPStatus

from allauth.account.models import EmailAddress
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from analytics.models import Hit, Session
from core.factories import ServiceFactory, UserFactory
from core.models import Service


def make_user(email):
    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


class ServiceViewTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = make_user("owner@example.com")
        self.collaborator = make_user("collab@example.com")
        self.stranger = make_user("stranger@example.com")
        self.service = ServiceFactory(owner=self.owner)
        self.service.collaborators.add(self.collaborator)
        now = timezone.now()
        self.session = Session.objects.create(
            service=self.service,
            ip="203.0.113.7",
            user_agent="x",
            browser="Firefox",
            os="Linux",
            device_type="DESKTOP",
            country="CH",
            latitude=47.4,
            longitude=8.5,
            start_time=now - timedelta(minutes=5),
            last_seen=now,
        )
        Hit.objects.create(
            session=self.session,
            service=self.service,
            initial=True,
            tracker="JS",
            location="https://site.example/a",
            referrer="https://ref.example/",
            start_time=now - timedelta(minutes=5),
            last_seen=now,
        )

    def url(self, name, **kwargs):
        return reverse(f"dashboard:{name}", kwargs=kwargs)


class DashboardListTests(ServiceViewTestCase):
    def test_owner_and_collaborator_see_service(self):
        for user in (self.owner, self.collaborator):
            self.client.force_login(user)
            response = self.client.get(self.url("dashboard"))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertContains(response, self.service.name)

    def test_stranger_does_not_see_service(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.url("dashboard"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotContains(response, self.service.name)

    def test_date_range_parameters(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.url("dashboard"), {"startDate": "2020-01-01", "endDate": "2020-01-31"}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)


class ServiceDetailTests(ServiceViewTestCase):
    def test_detail_renders_stats_for_owner_and_collaborator(self):
        for user in (self.owner, self.collaborator):
            self.client.force_login(user)
            response = self.client.get(self.url("service", pk=self.service.pk))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertContains(response, "ref.example")

    def test_detail_denied_for_stranger(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.url("service", pk=self.service.pk))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_detail_requires_login(self):
        response = self.client.get(self.url("service", pk=self.service.pk))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_session_list_and_detail(self):
        self.client.force_login(self.owner)
        listing = self.client.get(self.url("service_session_list", pk=self.service.pk))
        self.assertEqual(listing.status_code, HTTPStatus.OK)
        detail = self.client.get(
            self.url(
                "service_session", pk=self.service.pk, session_pk=self.session.pk
            )
        )
        self.assertEqual(detail.status_code, HTTPStatus.OK)
        self.assertContains(detail, "Firefox")

    def test_location_list(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url("service_location_list", pk=self.service.pk))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "site.example/a")

    def test_session_list_denied_for_stranger(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.url("service_session_list", pk=self.service.pk))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class ServiceCrudTests(ServiceViewTestCase):
    form_data = {
        "name": "My new site",
        "link": "https://site.example",
        "respect_dnt": "True",
        "collect_ips": "True",
        "ignored_ips": "10.0.0.1",
        "ignore_robots": "False",
        "hide_referrer_regex": "",
        "origins": "*",
        "collaborators": "",
        "script_inject": "",
    }

    def test_create_is_restricted_to_superusers_by_default(self):
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.get(self.url("service_create")).status_code,
            HTTPStatus.FORBIDDEN,
        )
        self.client.force_login(UserFactory(is_superuser=True))
        self.assertEqual(
            self.client.get(self.url("service_create")).status_code, HTTPStatus.OK
        )

    @override_settings(ONLY_SUPERUSERS_CREATE=False)
    def test_create_page_and_post(self):
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.get(self.url("service_create")).status_code, HTTPStatus.OK
        )
        response = self.client.post(self.url("service_create"), self.form_data)

        service = Service.objects.get(name="My new site")
        self.assertRedirects(response, self.url("service", pk=service.uuid))
        self.assertEqual(service.owner, self.owner)
        self.assertEqual(service.ignored_ips, "10.0.0.1")

    @override_settings(ONLY_SUPERUSERS_CREATE=False)
    def test_create_with_invalid_ip_shows_error(self):
        self.client.force_login(self.owner)
        data = dict(self.form_data, ignored_ips="nonsense")
        response = self.client.post(self.url("service_create"), data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Service.objects.filter(name="My new site").exists())

    def test_update_by_owner_refreshes_caches(self):
        self.client.force_login(self.owner)
        data = dict(
            self.form_data,
            name="Renamed",
            origins="https://a.example",
            script_inject="console.log(1)",
            collaborators="collab@example.com",
        )
        response = self.client.post(
            self.url("service_update", pk=self.service.pk), data
        )

        self.assertRedirects(response, self.url("service", pk=self.service.pk))
        self.service.refresh_from_db()
        self.assertEqual(self.service.name, "Renamed")
        self.assertEqual(list(self.service.collaborators.all()), [self.collaborator])
        self.assertEqual(
            cache.get(f"service_origins_{self.service.uuid}"), "https://a.example"
        )
        self.assertEqual(
            cache.get(f"script_inject_{self.service.uuid}"), "console.log(1)"
        )

    def test_update_form_prefills_collaborator_emails(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url("service_update", pk=self.service.pk))
        self.assertContains(response, "collab@example.com")

    def test_update_denied_for_collaborator_and_stranger(self):
        for user in (self.collaborator, self.stranger):
            self.client.force_login(user)
            response = self.client.post(
                self.url("service_update", pk=self.service.pk), self.form_data
            )
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.service.refresh_from_db()
        self.assertNotEqual(self.service.name, "My new site")

    def test_delete_by_owner(self):
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.get(self.url("service_delete", pk=self.service.pk)).status_code,
            HTTPStatus.OK,
        )
        self.assertNotContains(
            self.client.get(self.url("service_delete", pk=self.service.pk)),
            'name="origins"',
        )
        response = self.client.post(self.url("service_delete", pk=self.service.pk))
        self.assertRedirects(response, self.url("dashboard"))
        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())
        self.assertEqual(Session.objects.count(), 0)

    def test_delete_denied_for_collaborator(self):
        self.client.force_login(self.collaborator)
        response = self.client.post(self.url("service_delete", pk=self.service.pk))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())
