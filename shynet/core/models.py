import ipaddress
import re
import uuid

from secrets import token_urlsafe

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import TruncDate, TruncHour
from django.db.utils import NotSupportedError
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# How long a session a needs to go without an update to no longer be considered 'active' (i.e., currently online)
ACTIVE_USER_TIMEDELTA = timezone.timedelta(
    milliseconds=settings.SCRIPT_HEARTBEAT_FREQUENCY * 2
)
RESULTS_LIMIT = 300


def _default_uuid():
    return str(uuid.uuid4())


def _validate_network_list(networks: str):
    try:
        _parse_network_list(networks)
    except ValueError as e:
        raise ValidationError(str(e))


def _validate_regex(regex: str):
    try:
        re.compile(regex)
    except re.error:
        raise ValidationError(f"'{regex}' is not valid RegEx")


def _parse_network_list(networks: str):
    if len(networks.strip()) == 0:
        return []
    return [ipaddress.ip_network(network.strip()) for network in networks.split(",")]


def _default_api_token():
    return token_urlsafe(32)


class User(AbstractUser):
    username = models.TextField(default=_default_uuid, unique=True)
    email = models.EmailField(unique=True)
    api_token = models.TextField(default=_default_api_token, unique=True)

    def __str__(self):
        return self.email


class Service(models.Model):
    ACTIVE = "AC"
    ARCHIVED = "AR"
    SERVICE_STATUSES = [(ACTIVE, _("Active")), (ARCHIVED, _("Archived"))]

    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    name = models.TextField(max_length=64, verbose_name=_("Name"))
    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name="owning_services",
    )
    collaborators = models.ManyToManyField(
        User,
        verbose_name=_("Collaborators"),
        related_name="collaborating_services",
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("created"))
    link = models.URLField(blank=True, verbose_name=_("link"))
    origins = models.TextField(default="*", verbose_name=_("origins"))
    status = models.CharField(
        max_length=2,
        choices=SERVICE_STATUSES,
        default=ACTIVE,
        db_index=True,
        verbose_name=_("status"),
    )
    respect_dnt = models.BooleanField(default=True, verbose_name=_("Respect dnt"))
    ignore_robots = models.BooleanField(default=False, verbose_name=_("Ignore robots"))
    collect_ips = models.BooleanField(default=True, verbose_name=_("Collect ips"))
    ignored_ips = models.TextField(
        default="",
        blank=True,
        validators=[_validate_network_list],
        verbose_name=_("Igored ips"),
    )
    hide_referrer_regex = models.TextField(
        default="",
        blank=True,
        validators=[_validate_regex],
        verbose_name=_("Hide referrer regex"),
    )
    script_inject = models.TextField(
        default="", blank=True, verbose_name=_("Script inject")
    )

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["name", "uuid"]

    def __str__(self):
        return self.name

    def get_ignored_networks(self):
        return _parse_network_list(self.ignored_ips)

    def get_ignored_referrer_regex(self):
        if len(self.hide_referrer_regex.strip()) == 0:
            return re.compile(r".^")  # matches nothing
        else:
            try:
                return re.compile(self.hide_referrer_regex)
            except re.error:
                # Regexes are validated in the form, but this is an important
                # fallback to prevent form validation and malformed source
                # data from causing all service pages to error
                return re.compile(r".^")

    def get_daily_stats(self):
        return self.get_core_stats(
            start_time=timezone.now() - timezone.timedelta(days=1)
        )

    def get_core_stats(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = timezone.now() - timezone.timedelta(days=30)
        if end_time is None:
            end_time = timezone.now()

        main_data = self.get_relative_stats(start_time, end_time)
        comparison_data = self.get_relative_stats(
            start_time - (end_time - start_time), start_time
        )
        main_data["compare"] = comparison_data

        return main_data

    def get_relative_stats(self, start_time, end_time):
        Session = apps.get_model("analytics", "Session")
        Hit = apps.get_model("analytics", "Hit")

        tz_now = timezone.now()

        currently_online = Session.objects.filter(
            service=self, last_seen__gt=tz_now - ACTIVE_USER_TIMEDELTA
        ).count()

        sessions = Session.objects.filter(
            service=self, start_time__gt=start_time, start_time__lt=end_time
        ).order_by("-start_time")
        session_count = sessions.count()

        hits = Hit.objects.filter(
            service=self, start_time__lt=end_time, start_time__gt=start_time
        )
        hit_count = hits.count()

        has_hits = Hit.objects.filter(service=self).exists()

        bounces = sessions.filter(is_bounce=True)
        bounce_count = bounces.count()

        locations = (
            hits.values("location")
            .annotate(count=models.Count("location"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        referrer_ignore = self.get_ignored_referrer_regex()
        referrers = [
            referrer
            for referrer in (
                hits.filter(initial=True)
                .values("referrer")
                .annotate(count=models.Count("referrer"))
                .order_by("-count")[:RESULTS_LIMIT]
            )
            if not referrer_ignore.match(referrer["referrer"])
        ]

        countries = (
            sessions.values("country")
            .annotate(count=models.Count("country"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        operating_systems = (
            sessions.values("os")
            .annotate(count=models.Count("os"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        browsers = (
            sessions.values("browser")
            .annotate(count=models.Count("browser"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        device_types = (
            sessions.values("device_type")
            .annotate(count=models.Count("device_type"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        devices = (
            sessions.values("device")
            .annotate(count=models.Count("device"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        avg_load_time = hits.aggregate(load_time__avg=models.Avg("load_time"))[
            "load_time__avg"
        ]

        avg_hits_per_session = hit_count / session_count if session_count > 0 else None

        avg_session_duration = self._get_avg_session_duration(sessions, session_count)

        chart_data, chart_tooltip_format, chart_granularity = self._get_chart_data(
            sessions, hits, start_time, end_time, tz_now
        )

        return {
            "currently_online": currently_online,
            "session_count": session_count,
            "hit_count": hit_count,
            "has_hits": has_hits,
            "bounce_rate_pct": bounce_count * 100 / session_count
            if session_count > 0
            else None,
            "avg_session_duration": avg_session_duration,
            "avg_load_time": avg_load_time,
            "avg_hits_per_session": avg_hits_per_session,
            "locations": locations,
            "referrers": referrers,
            "countries": countries,
            "operating_systems": operating_systems,
            "browsers": browsers,
            "devices": devices,
            "device_types": device_types,
            "chart_data": chart_data,
            "chart_tooltip_format": chart_tooltip_format,
            "chart_granularity": chart_granularity,
            "online": True,
        }

    def _get_avg_session_duration(self, sessions, session_count):
        try:
            avg_session_duration = sessions.annotate(
                duration=models.F("last_seen") - models.F("start_time")
            ).aggregate(time_delta=models.Avg("duration"))["time_delta"]
        except NotSupportedError:
            avg_session_duration = sum(
                [
                    (session.last_seen - session.start_time).total_seconds()
                    for session in sessions
                ]
            ) / max(session_count, 1)
        if session_count == 0:
            avg_session_duration = None

        return avg_session_duration

    def _get_chart_data(self, sessions, hits, start_time, end_time, tz_now):
        # Show hourly chart for date ranges of 3 days or less, otherwise daily chart
        if (end_time - start_time).days < 3:
            chart_tooltip_format = "MM/dd HH:mm"
            chart_granularity = "hourly"
            sessions_per_hour = (
                sessions.annotate(hour=TruncHour("start_time"))
                .values("hour")
                .annotate(count=models.Count("uuid"))
                .order_by("hour")
            )
            chart_data = {
                k["hour"]: {"sessions": k["count"], "hits": 0}
                for k in sessions_per_hour
            }
            hits_per_hour = (
                hits.annotate(hour=TruncHour("start_time"))
                .values("hour")
                .annotate(count=models.Count("id"))
                .order_by("hour")
            )
            for k in hits_per_hour:
                if k["hour"] not in chart_data:
                    chart_data[k["hour"]] = {"hits": k["count"], "sessions": 0}
                else:
                    chart_data[k["hour"]]["hits"] = k["count"]

            hours_range = range(int((end_time - start_time).total_seconds() / 3600) + 1)
            for hour_offset in hours_range:
                hour = start_time + timezone.timedelta(hours=hour_offset)
                if hour not in chart_data and hour <= tz_now:
                    chart_data[hour] = {"sessions": 0, "hits": 0}
        else:
            chart_tooltip_format = "MMM d"
            chart_granularity = "daily"
            sessions_per_day = (
                sessions.annotate(date=TruncDate("start_time"))
                .values("date")
                .annotate(count=models.Count("uuid"))
                .order_by("date")
            )
            chart_data = {
                k["date"]: {"sessions": k["count"], "hits": 0} for k in sessions_per_day
            }
            hits_per_day = (
                hits.annotate(date=TruncDate("start_time"))
                .values("date")
                .annotate(count=models.Count("id"))
                .order_by("date")
            )
            for k in hits_per_day:
                if k["date"] not in chart_data:
                    chart_data[k["date"]] = {"hits": k["count"], "sessions": 0}
                else:
                    chart_data[k["date"]]["hits"] = k["count"]

            for day_offset in range((end_time - start_time).days + 1):
                day = (start_time + timezone.timedelta(days=day_offset)).date()
                if day not in chart_data and day <= tz_now.date():
                    chart_data[day] = {"sessions": 0, "hits": 0}

        chart_data = sorted(chart_data.items(), key=lambda k: k[0])
        chart_data = {
            "sessions": [v["sessions"] for k, v in chart_data],
            "hits": [v["hits"] for k, v in chart_data],
            "labels": [str(k) for k, v in chart_data],
        }

        return chart_data, chart_tooltip_format, chart_granularity

    def get_absolute_url(self):
        return reverse(
            "dashboard:service",
            kwargs={"pk": self.pk},
        )
