import datetime
import ipaddress
import re
import uuid
from secrets import token_urlsafe
from typing import Tuple, Optional

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.db.models.functions import TruncDate, TruncHour
from django.db.utils import NotSupportedError
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.constants import (
    ChartGranularity,
    ChartTooltipDateTimeFormat,
    ChartDataKeys,
    CoreConstants,
)

Session = apps.get_model("analytics", "Session")
Hit = apps.get_model("analytics", "Hit")

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
        raise ValidationError(str(e)) from e


def _validate_regex(regex: str):
    try:
        re.compile(regex)
    except re.error as e:
        raise ValidationError(f"'{regex}' is not valid RegEx") from e


def _parse_network_list(networks: str):
    return (
        [ipaddress.ip_network(network.strip()) for network in networks.split(",")]
        if networks.strip()
        else []
    )


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

    def get_core_stats(
        self,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
    ) -> dict:
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

    def _get_hits_data(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> Tuple[QuerySet, int, bool]:
        hits: QuerySet = Hit.objects.filter(
            service=self, start_time__lt=end_time, start_time__gt=start_time
        )
        hit_count: int = hits.count()
        has_hits: bool = Hit.objects.filter(service=self).exists()
        return hits, hit_count, has_hits

    def _get_avg_hits_data(
        self, hits: QuerySet, hit_count: int, session_count: int
    ) -> Tuple[Optional[float], Optional[float]]:
        avg_load_time: Optional[float] = hits.aggregate(
            load_time__avg=models.Avg("load_time")
        )["load_time__avg"]
        avg_hits_per_session: Optional[float] = (
            hit_count / session_count if session_count > 0 else None
        )
        return avg_load_time, avg_hits_per_session


    def _get_devices_data(self, sessions: QuerySet) -> Tuple[QuerySet, QuerySet]:
        device_types: QuerySet = (
            sessions.values("device_type")
            .annotate(count=models.Count("device_type"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        devices: QuerySet = (
            sessions.values("device")
            .annotate(count=models.Count("device"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        return device_types, devices


    def _get_bounces_data(self, sessions: QuerySet) -> Tuple[QuerySet, int]:
        bounces: QuerySet = sessions.filter(is_bounce=True)
        bounce_count: int = bounces.count()

        return bounces, bounce_count

    def _get_referrers(self, hits: QuerySet) -> list:
        referrer_ignore = self.get_ignored_referrer_regex()
        return [
            referrer
            for referrer in (
                hits.filter(initial=True)
                .values("referrer")
                .annotate(count=models.Count("referrer"))
                .order_by("-count")[:RESULTS_LIMIT]
            )
            if not referrer_ignore.match(referrer["referrer"])
        ]

    def get_relative_stats(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> dict:
        tz_now: datetime.datetime = timezone.now()

        currently_online: int = Session.objects.filter(
            service=self, last_seen__gt=tz_now - ACTIVE_USER_TIMEDELTA
        ).count()
        sessions: QuerySet = Session.objects.filter(
            service=self, start_time__gt=start_time, start_time__lt=end_time
        ).order_by("-start_time")

        session_count: int = sessions.count()
        countries: QuerySet = (
            sessions.values("country")
            .annotate(count=models.Count("country"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        operating_systems: QuerySet = (
            sessions.values("os")
            .annotate(count=models.Count("os"))
            .order_by("-count")[:RESULTS_LIMIT]

        )
        browsers: QuerySet = (
            sessions.values("browser")
            .annotate(count=models.Count("browser"))
            .order_by("-count")[:RESULTS_LIMIT]
        )
        avg_session_duration: Optional[float] = self._get_avg_session_duration(
            sessions, session_count
        )

        # get bounces data
        bounces, bounce_count = self._get_bounces_data(sessions)

        # get device data
        device_types, devices = self._get_devices_data(sessions)

        # get hits data
        hits, hit_count, has_hits = self._get_hits_data(start_time, end_time)

        # get locations
        locations: QuerySet = (
            hits.values("location")
            .annotate(count=models.Count("location"))
            .order_by("-count")[:RESULTS_LIMIT]
        )

        # get avg hits data
        avg_load_time, avg_hits_per_session = self._get_avg_hits_data(
            hits, hit_count, session_count
        )

        # get referrers
        referrers = self._get_referrers(hits)

        # get chart data
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

    def _get_avg_session_duration(
        self, sessions: QuerySet, session_count: int
    ) -> Optional[float]:
        try:
            avg_session_duration = sessions.annotate(
                duration=models.F("last_seen") - models.F("start_time")
            ).aggregate(time_delta=models.Avg("duration"))["time_delta"]
        except NotSupportedError:
            avg_session_duration = sum(
                (session.last_seen - session.start_time).total_seconds()
                for session in sessions
            ) / max(session_count, 1)

        if session_count == 0:
            avg_session_duration = None

        return avg_session_duration

    def _get_hits_data_for_chart(
        self, hits: QuerySet, chart_key: str, data: Optional[dict] = None
    ) -> dict:
        if not data:
            data = {}

        for hit in hits:
            if hit[chart_key] not in data:
                data[hit[chart_key]] = {"hits": hit["count"], "sessions": 0}
            else:
                data[hit[chart_key]]["hits"] = hit["count"]

        return data

    def _update_chart_data_for_offset(
        self,
        offset_range: range,
        current_tz: datetime.datetime,
        start_time: datetime.datetime,
        chart_type: str,
        data: Optional[dict] = None,
    ) -> dict:
        if not data:
            data = {}

        for offset in offset_range:
            # TODO: Is there a better way to do this?
            delta_dict = {
                CoreConstants.HOURS
                if chart_type == ChartGranularity.HOURLY
                else CoreConstants.DAYS: offset
            }
            offset_key = (start_time + timezone.timedelta(**delta_dict)).date()
            if offset_key not in data and offset_key <= current_tz.date():
                data[offset_key] = {"sessions": 0, "hits": 0}

        return data

    def _get_chart_data(
        self,
        sessions: QuerySet,
        hits: QuerySet,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        tz_now: datetime.datetime,
    ):
        # Show hourly chart for date ranges of 3 days or less, otherwise daily chart
        if (end_time - start_time).days < 3:
            chart_tooltip_format = ChartTooltipDateTimeFormat.HOURLY_TOOLTIP
            chart_granularity = ChartGranularity.HOURLY
            sessions_per_hour: QuerySet = (
                sessions.annotate(hour=TruncHour("start_time"))
                .values("hour")
                .annotate(count=models.Count("uuid"))
                .order_by("hour")
            )
            chart_data = {
                k["hour"]: {"sessions": k["count"], "hits": 0}
                for k in sessions_per_hour
            }
            hits_per_hour: QuerySet = (
                hits.annotate(hour=TruncHour("start_time"))
                .values("hour")
                .annotate(count=models.Count("id"))
                .order_by("hour")
            )

            chart_data = self._get_hits_data_for_chart(
                hits=hits_per_hour, chart_key=ChartDataKeys.HOUR, data=chart_data
            )

            hours_range = range(int((end_time - start_time).total_seconds() / 3600) + 1)
            chart_data = self._update_chart_data_for_offset(
                offset_range=hours_range,
                current_tz=tz_now,
                start_time=start_time,
                chart_type=chart_granularity,
                data=chart_data,
            )

        else:
            chart_tooltip_format = ChartTooltipDateTimeFormat.DAILY_TOOLTIP
            chart_granularity = ChartGranularity.DAILY
            sessions_per_day: QuerySet = (
                sessions.annotate(date=TruncDate("start_time"))
                .values("date")
                .annotate(count=models.Count("uuid"))
                .order_by("date")
            )
            chart_data = {
                k["date"]: {"sessions": k["count"], "hits": 0} for k in sessions_per_day
            }
            hits_per_day: QuerySet = (
                hits.annotate(date=TruncDate("start_time"))
                .values("date")
                .annotate(count=models.Count("id"))
                .order_by("date")
            )
            chart_data = self._get_hits_data_for_chart(
                hits=hits_per_day, chart_key=ChartDataKeys.DATE, data=chart_data
            )

            day_range = range((end_time - start_time).days + 1)
            chart_data = self._update_chart_data_for_offset(
                offset_range=day_range,
                current_tz=tz_now,
                start_time=start_time,
                chart_type=chart_granularity,
                data=chart_data,
            )

        sorted_chart_data = sorted(chart_data.items(), key=lambda k: k[0])
        final_chart_data = {
            "sessions": [v["sessions"] for k, v in sorted_chart_data],
            "hits": [v["hits"] for k, v in sorted_chart_data],
            "labels": [str(k) for k, v in sorted_chart_data],
        }

        return final_chart_data, chart_tooltip_format, chart_granularity

    def get_absolute_url(self):
        return reverse(
            "dashboard:service",
            kwargs={"pk": self.pk},
        )
