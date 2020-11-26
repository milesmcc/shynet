import json
import uuid

from django.db import models
from django.shortcuts import reverse
from django.utils import timezone

from core.models import Service


def _default_uuid():
    return str(uuid.uuid4())


class Session(models.Model):
    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_index=True)

    # Cross-session identification; optional, and provided by the service
    identifier = models.TextField(blank=True, db_index=True)

    # Time
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now)

    # Core request information
    user_agent = models.TextField()
    browser = models.TextField()
    device = models.TextField()
    device_type = models.CharField(
        max_length=7,
        choices=[
            ("PHONE", "Phone"),
            ("TABLET", "Tablet"),
            ("DESKTOP", "Desktop"),
            ("ROBOT", "Robot"),
            ("OTHER", "Other"),
        ],
        default="OTHER",
    )
    os = models.TextField()
    ip = models.GenericIPAddressField(db_index=True, null=True)

    # GeoIP data
    asn = models.TextField(blank=True)
    country = models.TextField(blank=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    time_zone = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["service", "-start_time"]),
            models.Index(fields=["service", "identifier"]),
        ]

    @property
    def is_currently_active(self):
        return timezone.now() - self.last_seen < timezone.timedelta(seconds=10)

    @property
    def duration(self):
        return self.last_seen - self.start_time

    def __str__(self):
        return f"{self.identifier if self.identifier != '' else 'Anonymous'} @ {self.service.name} [{str(self.uuid)[:6]}]"

    def get_absolute_url(self):
        return reverse(
            "dashboard:service_session",
            kwargs={"pk": self.service.pk, "session_pk": self.uuid},
        )


class Hit(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, db_index=True)
    initial = models.BooleanField(default=True, db_index=True)

    # Base request information
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now)
    heartbeats = models.IntegerField(default=0)
    tracker = models.TextField(
        choices=[("JS", "JavaScript"), ("PIXEL", "Pixel (noscript)")]
    )  # Tracking pixel or JS

    # Advanced page information
    location = models.TextField(blank=True, db_index=True)
    referrer = models.TextField(blank=True, db_index=True)
    load_time = models.FloatField(null=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["session", "-start_time"]),
            models.Index(fields=["session", "location"]),
            models.Index(fields=["session", "referrer"]),
        ]

    @property
    def duration(self):
        return self.last_seen - self.start_time

    def get_absolute_url(self):
        return reverse(
            "dashboard:service_session",
            kwargs={"pk": self.session.service.pk, "session_pk": self.session.pk},
        )
