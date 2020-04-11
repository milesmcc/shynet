import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.apps import apps
from django.utils import timezone
from django.db.utils import NotSupportedError


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

    # Analytics settings
    anonymize_ips = models.BooleanField(default=False)

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
        )
        session_count = sessions.count()

        hits = Hit.objects.filter(
            session__service=self, start_time__lt=end_time, start_time__gt=start_time
        )
        hit_count = hits.count()

        bounces = sessions.annotate(hit_count=models.Count("hit")).filter(hit_count=1)
        bounce_count = bounces.count()

        try:
            avg_session_duration = sessions.annotate(
                duration=models.F("last_seen") - models.F("start_time")
            ).aggregate(duration=models.Avg("duration"))["duration"]
        except NotSupportedError:
            avg_session_duration = (
                sum(
                    [
                        (session.last_seen - session.start_time).total_seconds()
                        for session in sessions
                    ]
                )
                / session_count
            )

        return {
            "currently_online": currently_online,
            "sessions": session_count,
            "hits": hit_count,
            "avg_hits_per_session": hit_count / (max(session_count, 1)),
            "bounce_rate_pct": bounce_count * 100 / session_count,
            "avg_session_duration": avg_session_duration,
            "uptime": 99.9,
            "online": True,
        }
