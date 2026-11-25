from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from analytics.models import Hit, Session
from core.factories import ServiceFactory, UserFactory
from core.models import Service, _default_api_token


class UserTests(TestCase):
    def test_str_is_email(self):
        self.assertEqual(str(UserFactory(email="a@example.com")), "a@example.com")

    def test_api_tokens_are_unique_and_long(self):
        first, second = _default_api_token(), _default_api_token()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 32)
        self.assertNotEqual(UserFactory().api_token, UserFactory().api_token)


class ServiceValidationTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()

    def make(self, **kwargs):
        return Service(name="s", owner=self.owner, **kwargs)

    def test_valid_ignored_ips(self):
        service = self.make(ignored_ips="192.168.0.2, 10.0.0.0/8, 2001:db8::/32")
        service.full_clean()
        self.assertEqual(len(service.get_ignored_networks()), 3)

    def test_invalid_ignored_ips_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.make(ignored_ips="999.1.1.1").full_clean()

    def test_empty_ignored_ips(self):
        self.assertEqual(self.make(ignored_ips=" ").get_ignored_networks(), [])

    def test_invalid_regex_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.make(hide_referrer_regex="(").full_clean()

    def test_referrer_regex(self):
        service = self.make(hide_referrer_regex=r"^https://hidden\.")
        regex = service.get_ignored_referrer_regex()
        self.assertTrue(regex.search("https://hidden.example/"))
        self.assertFalse(regex.search("https://shown.example/"))

    def test_empty_or_broken_regex_matches_nothing(self):
        for value in ["", "   ", "("]:
            regex = self.make(hide_referrer_regex=value).get_ignored_referrer_regex()
            self.assertFalse(regex.search("anything"))

    def test_defaults(self):
        service = ServiceFactory(owner=self.owner)
        self.assertEqual(service.status, Service.ACTIVE)
        self.assertEqual(service.origins, "*")
        self.assertTrue(service.respect_dnt)
        self.assertTrue(service.collect_ips)
        self.assertFalse(service.ignore_robots)

    def test_absolute_url(self):
        service = ServiceFactory(owner=self.owner)
        self.assertIn(str(service.uuid), service.get_absolute_url())


class ServiceStatsTests(TestCase):
    def setUp(self):
        self.service = ServiceFactory(owner=UserFactory())
        self.now = timezone.now()

    def add_session(self, minutes_ago, hits=1, **kwargs):
        start = self.now - timedelta(minutes=minutes_ago)
        defaults = dict(
            ip="203.0.113.7",
            user_agent="x",
            browser="Firefox",
            device="",
            device_type="DESKTOP",
            os="Linux",
            asn="Example AG",
            country="CH",
            time_zone="Europe/Zurich",
            start_time=start,
            last_seen=start + timedelta(minutes=1),
        )
        defaults.update(kwargs)
        session = Session.objects.create(service=self.service, **defaults)
        for i in range(hits):
            Hit.objects.create(
                session=session,
                service=self.service,
                initial=(i == 0),
                tracker="JS",
                location=f"https://site.example/page{i}",
                referrer="https://ref.example/" if i == 0 else "",
                start_time=start,
                last_seen=start,
            )
        session.recalculate_bounce()
        return session

    def test_empty_service_has_zero_stats(self):
        stats = self.service.get_core_stats()
        self.assertEqual(stats["session_count"], 0)
        self.assertEqual(stats["hit_count"], 0)

    def test_core_stats_counts_and_breakdowns(self):
        self.add_session(10, hits=2)
        self.add_session(20, hits=1, browser="Chrome", country="DE")

        stats = self.service.get_core_stats(
            start_time=self.now - timedelta(hours=1), end_time=self.now
        )

        self.assertEqual(stats["session_count"], 2)
        self.assertEqual(stats["hit_count"], 3)
        self.assertEqual(stats["bounce_rate_pct"], 50)
        self.assertEqual(stats["currently_online"], 0)
        browsers = {row["browser"]: row["count"] for row in stats["browsers"]}
        self.assertEqual(browsers, {"Firefox": 1, "Chrome": 1})
        countries = {row["country"]: row["count"] for row in stats["countries"]}
        self.assertEqual(countries, {"CH": 1, "DE": 1})
        self.assertIn("chart_data", stats)

    def test_stats_exclude_other_services_and_old_sessions(self):
        self.add_session(10)
        self.add_session(60 * 24 * 10)
        other = ServiceFactory(owner=self.service.owner)
        Session.objects.create(
            service=other, start_time=self.now, last_seen=self.now, user_agent="x"
        )

        stats = self.service.get_core_stats(
            start_time=self.now - timedelta(hours=1), end_time=self.now
        )
        self.assertEqual(stats["session_count"], 1)

    def test_daily_stats_and_relative_stats_run(self):
        self.add_session(10)
        self.assertEqual(self.service.get_daily_stats()["session_count"], 1)
        relative = self.service.get_relative_stats(
            self.now - timedelta(days=1), self.now
        )
        self.assertIn("session_count", relative)
        self.assertIn("hit_count", relative)

    def test_referrer_regex_hides_referrers(self):
        self.add_session(10)
        self.service.hide_referrer_regex = r"https://ref\."
        self.service.save()
        stats = self.service.get_core_stats(
            start_time=self.now - timedelta(hours=1), end_time=self.now
        )
        self.assertEqual(list(stats["referrers"]), [])
