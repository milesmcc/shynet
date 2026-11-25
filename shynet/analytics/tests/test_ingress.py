import json
from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from analytics.models import Hit, Session
from core.factories import ServiceFactory, UserFactory
from core.models import Service

CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
GOOGLEBOT = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)


class IngressTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = UserFactory()
        self.service = ServiceFactory(owner=self.owner)
        self.pixel = reverse(
            "ingress:endpoint_pixel", kwargs={"service_uuid": self.service.uuid}
        )
        self.script = reverse(
            "ingress:endpoint_script", kwargs={"service_uuid": self.service.uuid}
        )

    def hit_pixel(self, ua=CHROME, ip="203.0.113.7", **extra):
        return self.client.get(
            self.pixel, HTTP_USER_AGENT=ua, REMOTE_ADDR=ip, **extra
        )

    def post_script(self, payload=None, ua=CHROME, ip="203.0.113.7", **extra):
        return self.client.post(
            self.script,
            data=json.dumps(payload or {}),
            content_type="application/json",
            HTTP_USER_AGENT=ua,
            REMOTE_ADDR=ip,
            **extra,
        )


class PixelViewTests(IngressTestCase):
    def test_returns_gif_and_records_session_and_hit(self):
        response = self.hit_pixel(HTTP_REFERER="https://example.com/page")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "image/gif")
        self.assertTrue(response.content.startswith(b"GIF89a"))
        self.assertIn("no-cache", response["Cache-Control"])
        session = Session.objects.get()
        hit = Hit.objects.get()
        self.assertEqual(str(session.service_id), str(self.service.pk))
        self.assertEqual(hit.session, session)
        self.assertEqual(hit.tracker, "PIXEL")
        self.assertTrue(hit.initial)
        self.assertEqual(hit.location, "https://example.com/page")

    def test_identifier_is_stored_on_session(self):
        url = reverse(
            "ingress:endpoint_pixel_id",
            kwargs={"service_uuid": self.service.uuid, "identifier": "blog"},
        )
        self.client.get(url, HTTP_USER_AGENT=CHROME, REMOTE_ADDR="203.0.113.7")

        self.assertEqual(Session.objects.get().identifier, "blog")

    def test_unknown_service_returns_404(self):
        url = reverse(
            "ingress:endpoint_pixel",
            kwargs={"service_uuid": "00000000-0000-0000-0000-000000000000"},
        )
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.NOT_FOUND)

    def test_malformed_service_uuid_returns_400(self):
        url = reverse("ingress:endpoint_pixel", kwargs={"service_uuid": "nope"})
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.BAD_REQUEST)

    def test_archived_service_records_nothing(self):
        Service.objects.filter(pk=self.service.pk).update(status=Service.ARCHIVED)
        self.hit_pixel()
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(Hit.objects.count(), 0)


class OriginTests(IngressTestCase):
    def set_origins(self, origins):
        Service.objects.filter(pk=self.service.pk).update(origins=origins)
        cache.clear()

    def test_wildcard_origin_allows_everything(self):
        response = self.post_script({}, HTTP_ORIGIN="https://anything.example")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertIn("POST", response["Access-Control-Allow-Methods"])

    def test_listed_origin_is_allowed_case_insensitively(self):
        self.set_origins("https://a.example, https://B.example")
        response = self.post_script({}, HTTP_ORIGIN="https://b.example")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Hit.objects.count(), 1)

    def test_unlisted_origin_is_forbidden(self):
        self.set_origins("https://a.example")
        response = self.post_script({}, HTTP_ORIGIN="https://evil.example")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(Hit.objects.count(), 0)

    def test_origin_is_derived_from_referer(self):
        self.set_origins("https://a.example")
        response = self.post_script({}, HTTP_REFERER="https://a.example/some/page")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Hit.objects.count(), 1)

    def test_missing_origin_is_forbidden_when_restricted(self):
        self.set_origins("https://a.example")
        self.assertEqual(self.post_script({}).status_code, HTTPStatus.FORBIDDEN)


class ScriptViewTests(IngressTestCase):
    def test_get_serves_javascript_with_endpoint(self):
        response = self.client.get(self.script)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertIn("max-age=31536000", response["Cache-Control"])
        self.assertIn(self.script, response.content.decode())

    def test_get_with_identifier_uses_identifier_endpoint(self):
        url = reverse(
            "ingress:endpoint_script_id",
            kwargs={"service_uuid": self.service.uuid, "identifier": "shop"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(url, response.content.decode())

    def test_get_injects_custom_script(self):
        Service.objects.filter(pk=self.service.pk).update(
            script_inject="console.log('custom-inject-marker');"
        )
        response = self.client.get(self.script)
        self.assertIn("custom-inject-marker", response.content.decode())

    def test_post_records_js_hit_with_payload(self):
        response = self.post_script(
            {
                "referrer": "https://ref.example/",
                "location": "https://site.example/p",
                "loadTime": 123.5,
            }
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content), {"status": "OK"})
        hit = Hit.objects.get()
        self.assertEqual(hit.tracker, "JS")
        self.assertEqual(hit.referrer, "https://ref.example/")
        self.assertEqual(hit.location, "https://site.example/p")
        self.assertEqual(hit.load_time, 123.5)

    def test_post_with_non_positive_load_time_stores_none(self):
        self.post_script({"loadTime": 0})
        self.assertIsNone(Hit.objects.get().load_time)

    def test_heartbeat_updates_existing_hit(self):
        self.post_script({"idempotency": "abc"})
        self.post_script({"idempotency": "abc"})
        self.post_script({"idempotency": "abc"})

        hit = Hit.objects.get()
        self.assertEqual(hit.heartbeats, 2)
        self.assertEqual(Session.objects.count(), 1)

    def test_different_idempotency_creates_new_hit_in_same_session(self):
        self.post_script({"idempotency": "one"})
        self.post_script({"idempotency": "two"})

        self.assertEqual(Hit.objects.count(), 2)
        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(Hit.objects.filter(initial=True).count(), 1)

    def test_invalid_json_body_raises(self):
        with self.assertRaises(ValueError):
            self.client.post(
                self.script, data="not json", content_type="application/json"
            )


class PrivacyTests(IngressTestCase):
    def test_dnt_is_ignored_when_service_respects_it(self):
        self.hit_pixel(HTTP_DNT="1")
        self.assertEqual(Session.objects.count(), 0)

    def test_gpc_is_ignored_when_service_respects_it(self):
        self.hit_pixel(HTTP_SEC_GPC="1")
        self.assertEqual(Session.objects.count(), 0)

    def test_dnt_is_recorded_when_service_does_not_respect_it(self):
        Service.objects.filter(pk=self.service.pk).update(respect_dnt=False)
        self.hit_pixel(HTTP_DNT="1")
        self.assertEqual(Session.objects.count(), 1)

    def test_script_get_reflects_dnt_for_respecting_service(self):
        with_dnt = self.client.get(self.script, HTTP_DNT="1").content.decode()
        without = self.client.get(self.script).content.decode()
        self.assertNotEqual(with_dnt, without)

    def test_ip_is_stored_by_default(self):
        self.hit_pixel(ip="203.0.113.7")
        self.assertEqual(Session.objects.get().ip, "203.0.113.7")

    def test_ip_is_not_stored_when_collection_disabled(self):
        Service.objects.filter(pk=self.service.pk).update(collect_ips=False)
        self.hit_pixel(ip="203.0.113.7")
        self.assertIsNone(Session.objects.get().ip)

    def test_ignored_ip_network_is_skipped(self):
        Service.objects.filter(pk=self.service.pk).update(
            ignored_ips="203.0.113.0/24, 2001:db8::/32"
        )
        self.hit_pixel(ip="203.0.113.7")
        self.hit_pixel(ip="2001:db8::1")
        self.assertEqual(Session.objects.count(), 0)

        self.hit_pixel(ip="198.51.100.9")
        self.assertEqual(Session.objects.count(), 1)


class SessionTests(IngressTestCase):
    def test_same_visitor_reuses_session(self):
        self.hit_pixel()
        self.hit_pixel()

        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(Hit.objects.count(), 2)
        self.assertEqual(Hit.objects.filter(initial=True).count(), 1)

    def test_different_ip_or_user_agent_creates_new_session(self):
        self.hit_pixel(ip="203.0.113.7")
        self.hit_pixel(ip="203.0.113.8")
        self.hit_pixel(ip="203.0.113.7", ua=IPHONE)

        self.assertEqual(Session.objects.count(), 3)

    def test_session_is_not_shared_between_services(self):
        other = ServiceFactory(owner=self.owner)
        self.hit_pixel()
        self.client.get(
            reverse("ingress:endpoint_pixel", kwargs={"service_uuid": other.uuid}),
            HTTP_USER_AGENT=CHROME,
            REMOTE_ADDR="203.0.113.7",
        )
        self.assertEqual(Session.objects.count(), 2)

    def test_identifier_is_filled_in_later(self):
        self.hit_pixel()
        url = reverse(
            "ingress:endpoint_pixel_id",
            kwargs={"service_uuid": self.service.uuid, "identifier": "late"},
        )
        self.client.get(url, HTTP_USER_AGENT=CHROME, REMOTE_ADDR="203.0.113.7")

        self.assertEqual(Session.objects.get().identifier, "late")

    def test_bounce_is_recalculated(self):
        self.hit_pixel()
        self.assertTrue(Session.objects.get().is_bounce)
        self.hit_pixel()
        self.assertFalse(Session.objects.get().is_bounce)


class UserAgentTests(IngressTestCase):
    def assert_session(self, ua, browser, os, device_type):
        self.hit_pixel(ua=ua)
        session = Session.objects.get()
        self.assertEqual(session.browser, browser)
        self.assertEqual(session.os, os)
        self.assertEqual(session.device_type, device_type)

    def test_desktop_chrome(self):
        self.assert_session(CHROME, "Chrome", "Windows", "DESKTOP")

    def test_iphone_is_phone(self):
        self.assert_session(IPHONE, "Mobile Safari", "iOS", "PHONE")

    def test_googlebot_is_robot(self):
        self.hit_pixel(ua=GOOGLEBOT)
        self.assertEqual(Session.objects.get().device_type, "ROBOT")

    def test_robots_are_skipped_when_service_ignores_them(self):
        Service.objects.filter(pk=self.service.pk).update(ignore_robots=True)
        self.hit_pixel(ua=GOOGLEBOT)
        self.assertEqual(Session.objects.count(), 0)
        self.hit_pixel(ua=CHROME)
        self.assertEqual(Session.objects.count(), 1)
