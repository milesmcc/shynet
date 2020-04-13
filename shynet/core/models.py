import json
import uuid

from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import TruncDate
from django.db.utils import NotSupportedError
from django.utils import timezone


def _default_uuid():
    return str(uuid.uuid4())


class User(AbstractUser):
    username = models.TextField(default=_default_uuid, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Service(models.Model):
    ACTIVE = "AC"
    ARCHIVED = "AR"
    SERVICE_STATUSES = [(ACTIVE, "Active"), (ARCHIVED, "Archived")]

    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    name = models.TextField(max_length=64)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owning_services"
    )
    collaborators = models.ManyToManyField(
        User, related_name="collaborating_services", blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True)
    origins = models.TextField(default="*")
    status = models.CharField(
        max_length=2, choices=SERVICE_STATUSES, default=ACTIVE, db_index=True
    )

    def __str__(self):
        return self.name

    def get_daily_stats(self):
        return self.get_core_stats(
            start_time=timezone.now() - timezone.timedelta(days=1)
        )

    def get_core_stats(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = timezone.now() - timezone.timedelta(days=30)
        if end_time is None:
            end_time = timezone.now()

        Session = apps.get_model("analytics", "Session")
        Hit = apps.get_model("analytics", "Hit")

        currently_online = Session.objects.filter(
            service=self, start_time__gt=timezone.now() - timezone.timedelta(seconds=10)
        ).count()

        sessions = Session.objects.filter(
            service=self, start_time__gt=start_time, start_time__lt=end_time
        ).order_by("-start_time")
        session_count = sessions.count()

        hits = Hit.objects.filter(
            session__service=self, start_time__lt=end_time, start_time__gt=start_time
        )
        hit_count = hits.count()

        bounces = sessions.annotate(hit_count=models.Count("hit")).filter(hit_count=1)
        bounce_count = bounces.count()

        locations = (
            hits.values("location")
            .annotate(count=models.Count("location"))
            .order_by("-count")
        )

        referrers = (
            hits.filter(initial=True)
            .values("referrer")
            .annotate(count=models.Count("referrer"))
            .order_by("-count")
        )

        operating_systems = (
            sessions.values("os").annotate(count=models.Count("os")).order_by("-count")
        )

        browsers = (
            sessions.values("browser")
            .annotate(count=models.Count("browser"))
            .order_by("-count")
        )

        device_types = (
            sessions.values("device_type")
            .annotate(count=models.Count("device_type"))
            .order_by("-count")
        )

        devices = (
            sessions.values("device")
            .annotate(count=models.Count("device"))
            .order_by("-count")
        )

        device_types = (
            sessions.values("device_type")
            .annotate(count=models.Count("device_type"))
            .order_by("-count")
        )

        avg_load_time = hits.aggregate(load_time__avg=models.Avg("load_time"))[
            "load_time__avg"
        ]

        avg_hits_per_session = hit_count / session_count if session_count > 0 else None

        try:
            avg_session_duration = sessions.annotate(
                duration=models.F("last_seen") - models.F("start_time")
            ).aggregate(duration=models.Avg("duration"))["duration"]
        except NotSupportedError:
            avg_session_duration = sum(
                [
                    (session.last_seen - session.start_time).total_seconds()
                    for session in sessions
                ]
            ) / max(session_count, 1)
        if session_count == 0:
            avg_session_duration = None

        session_chart_data = {
            k["date"]: k["count"]
            for k in sessions.annotate(date=TruncDate("start_time"))
            .values("date")
            .annotate(count=models.Count("uuid"))
            .order_by("date")
        }
        for day_offset in range((end_time - start_time).days + 1):
            day = (start_time + timezone.timedelta(days=day_offset)).date()
            if day not in session_chart_data:
                session_chart_data[day] = 0

        return {
            "currently_online": currently_online,
            "session_count": session_count,
            "hit_count": hit_count,
            "avg_hits_per_session": hit_count / (max(session_count, 1)),
            "bounce_rate_pct": bounce_count * 100 / session_count
            if session_count > 0
            else None,
            "avg_session_duration": avg_session_duration,
            "avg_load_time": avg_load_time,
            "avg_hits_per_session": avg_hits_per_session,
            "locations": locations,
            "referrers": referrers,
            "operating_systems": operating_systems,
            "browsers": browsers,
            "devices": devices,
            "device_types": device_types,
            "session_chart_data": json.dumps(
                [
                    {"x": str(key), "y": value}
                    for key, value in session_chart_data.items()
                ]
            ),
            "online": True,
        }
