from datetime import timedelta
from unittest import mock

import geoip2.errors
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from analytics import tasks
from analytics.models import Hit, Session
from core.factories import ServiceFactory, UserFactory


class GeoIpLookupTests(SimpleTestCase):
    def setUp(self):
        tasks._geoip2_city_reader = None
        tasks._geoip2_asn_reader = None
        self.addCleanup(setattr, tasks, "_geoip2_city_reader", None)
        self.addCleanup(setattr, tasks, "_geoip2_asn_reader", None)

    def test_disabled_without_databases(self):
        with override_settings(MAXMIND_CITY_DB=None, MAXMIND_ASN_DB=None):
            self.assertIsNone(tasks._geoip2_lookup("203.0.113.7"))

    def test_lookup_maps_reader_results(self):
        city = mock.Mock()
        city.city.return_value.country.iso_code = "CH"
        city.city.return_value.location.longitude = 8.5
        city.city.return_value.location.latitude = 47.4
        city.city.return_value.location.time_zone = "Europe/Zurich"
        asn = mock.Mock()
        asn.asn.return_value.autonomous_system_organization = "Example AG"
        with mock.patch("geoip2.database.Reader", side_effect=[city, asn]):
            result = tasks._geoip2_lookup("203.0.113.7")

        self.assertEqual(
            result,
            {
                "asn": "Example AG",
                "country": "CH",
                "longitude": 8.5,
                "latitude": 47.4,
                "time_zone": "Europe/Zurich",
            },
        )

    def test_unknown_address_returns_empty_dict(self):
        reader = mock.Mock()
        reader.city.side_effect = geoip2.errors.AddressNotFoundError("nope")
        with mock.patch("geoip2.database.Reader", return_value=reader):
            self.assertEqual(tasks._geoip2_lookup("10.0.0.1"), {})

    def test_missing_database_file_returns_empty_dict(self):
        with mock.patch("geoip2.database.Reader", side_effect=FileNotFoundError("x")):
            with self.assertLogs("analytics.tasks", level="ERROR"):
                self.assertEqual(tasks._geoip2_lookup("203.0.113.7"), {})


@mock.patch(
    "analytics.tasks._geoip2_lookup",
    return_value={
        "asn": "Example AG",
        "country": "CH",
        "longitude": 8.5,
        "latitude": 47.4,
        "time_zone": "Europe/Zurich",
    },
)
class IngressRequestTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.service = ServiceFactory(owner=UserFactory())

    def run_task(self, **overrides):
        args = dict(
            service_uuid=str(self.service.uuid),
            tracker="JS",
            time=timezone.now(),
            payload={},
            ip="203.0.113.7",
            location="https://site.example/",
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        )
        args.update(overrides)
        return tasks.ingress_request(**args)

    def test_geoip_data_is_stored_on_session(self, _lookup):
        self.run_task()
        session = Session.objects.get()
        self.assertEqual(session.asn, "Example AG")
        self.assertEqual(session.country, "CH")
        self.assertEqual(session.time_zone, "Europe/Zurich")
        self.assertEqual(session.longitude, 8.5)
        self.assertEqual(session.latitude, 47.4)
        self.assertEqual(session.browser, "Firefox")
        self.assertEqual(session.device_type, "DESKTOP")

    def test_session_times_follow_task_time(self, _lookup):
        first = timezone.now() - timedelta(minutes=5)
        later = first + timedelta(minutes=2)
        self.run_task(time=first)
        self.run_task(time=later)

        session = Session.objects.get()
        self.assertEqual(session.start_time, first)
        self.assertEqual(session.last_seen, later)
        self.assertEqual(session.duration, timedelta(minutes=2))

    def test_unknown_service_raises(self, _lookup):
        with self.assertRaises(Exception):
            self.run_task(service_uuid="00000000-0000-0000-0000-000000000000")

    def test_aggressive_salting_changes_association(self, _lookup):
        with override_settings(AGGRESSIVE_HASH_SALTING=False):
            self.run_task()
            self.run_task()
        self.assertEqual(Session.objects.count(), 1)

    def test_block_all_ips_overrides_service_setting(self, _lookup):
        with override_settings(BLOCK_ALL_IPS=True):
            self.run_task()
        self.assertIsNone(Session.objects.get().ip)

    def test_hit_defaults(self, _lookup):
        self.run_task(tracker="PIXEL", payload={})
        hit = Hit.objects.get()
        self.assertEqual(hit.tracker, "PIXEL")
        self.assertEqual(hit.referrer, "")
        self.assertEqual(hit.location, "https://site.example/")
        self.assertEqual(hit.heartbeats, 0)
