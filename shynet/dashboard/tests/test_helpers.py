from datetime import timedelta
from types import SimpleNamespace

from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

from dashboard.templatetags import helpers


class FilterTests(SimpleTestCase):
    def test_naturaldelta(self):
        self.assertEqual(helpers.naturaldelta(timedelta(seconds=75)), "01:15")
        self.assertEqual(helpers.naturaldelta(3725), "01:02:05")
        self.assertEqual(helpers.naturaldelta(0), "00:00")

    def test_flag_class(self):
        self.assertEqual(helpers.flag_class("CH"), "mr-1 fi fi-ch")
        self.assertEqual(helpers.flag_class(""), "hidden")

    def test_country_helpers(self):
        self.assertEqual(helpers.country_name("CH"), "Switzerland")
        self.assertEqual(helpers.datamap_id("CH"), "CHE")
        self.assertEqual(helpers.country_name("ZZ"), "Unknown")
        self.assertEqual(helpers.datamap_id(None), "UNKNOWN")

    def test_percent(self):
        self.assertEqual(helpers.percent(1, 4), "25.0%")
        self.assertEqual(helpers.percent(1, 0), "N/A")
        self.assertEqual(helpers.percent(1, 100000), "<0.1%")

    @override_settings(USE_RELATIVE_MAX_IN_BAR_VISUALIZATION=False)
    def test_bar_width_relative_to_total(self):
        self.assertEqual(helpers.bar_width(5, 10, 20), "25.0%")
        self.assertEqual(helpers.bar_width(5, 0, 20), "0")

    @override_settings(USE_RELATIVE_MAX_IN_BAR_VISUALIZATION=True)
    def test_bar_width_relative_to_max(self):
        self.assertEqual(helpers.bar_width(5, 10, 20), "50.0%")

    def test_startswith(self):
        self.assertTrue(helpers.startswith("hello", "he"))
        self.assertFalse(helpers.startswith(None, "he"))

    def test_relative_stat_tone(self):
        self.assertEqual(helpers.relative_stat_tone(1, 2), "~positive")
        self.assertEqual(helpers.relative_stat_tone(2, 1), "~critical")
        self.assertEqual(helpers.relative_stat_tone(2, 1, good="DOWN"), "~positive")
        self.assertEqual(helpers.relative_stat_tone(1, 1), "~neutral")
        self.assertEqual(helpers.relative_stat_tone(None, 1), "~neutral")

    def test_percent_change_display(self):
        self.assertEqual(str(helpers.percent_change_display(100, 150)), "&uarr; 50%")
        self.assertEqual(str(helpers.percent_change_display(100, 50)), "&darr; 50%")
        self.assertEqual(str(helpers.percent_change_display(0, 5)), "&uarr; 100%")
        self.assertEqual(str(helpers.percent_change_display(1, 5000)), "> 999%")
        self.assertIn("n/a", str(helpers.percent_change_display(None, 5)))

    def test_location_url(self):
        session = SimpleNamespace(latitude=47.4, longitude=8.5)
        url = helpers.location_url(session)
        self.assertIn("47.4", url)
        self.assertIn("8.5", url)


class IconAndUrlTests(SimpleTestCase):
    @override_settings(SHOW_THIRD_PARTY_ICONS=False)
    def test_icons_disabled(self):
        self.assertEqual(helpers.iconify("Chrome"), "")

    @override_settings(SHOW_THIRD_PARTY_ICONS=True)
    def test_icons_enabled(self):
        self.assertIn("www.apple.com", helpers.iconify("Safari"))
        self.assertIn("foo.com.ico", helpers.iconify("foo"))
        self.assertIn("example.org.ico", helpers.iconify("https://example.org/x"))

    @override_settings(SHOW_THIRD_PARTY_ICONS=False)
    def test_urldisplay_escapes_and_strips_scheme(self):
        out = helpers.urldisplay("https://example.org/?a=<b>")
        self.assertIn("example.org/?a=&lt;b&gt;", out)
        self.assertNotIn("<b>", out)
        self.assertEqual(helpers.urldisplay("not a url"), "not a url")

    def test_filters_load_in_templates(self):
        template = Template(
            "{% load helpers %}{{ 75|naturaldelta }} {{ 'CH'|country_name }}"
        )
        self.assertEqual(template.render(Context()), "01:15 Switzerland")
