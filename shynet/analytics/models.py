import json
import uuid

from django.db import models
from django.utils import timezone

from core.models import Service


def _default_uuid():
    return str(uuid.uuid4())


class Session(models.Model):
    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    # Cross-session identification; optional, and provided by the service
    identifier = models.TextField(blank=True)

    # Time
    start_time = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)

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
    ip = models.GenericIPAddressField()

    # GeoIP data
    asn = models.TextField(blank=True)
    country = models.TextField(blank=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    time_zone = models.TextField(blank=True)

    @property
    def is_currently_active(self):
        return timezone.now() - self.last_seen < timezone.timedelta(seconds=10)

    @property
    def duration(self):
        return self.last_seen - self.start_time


class Hit(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    initial = models.BooleanField(default=True)

    # Base request information
    start_time = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)
    heartbeats = models.IntegerField(default=0)
    tracker = models.TextField()  # Tracking pixel or JS

    # Advanced page information
    location = models.TextField(blank=True)
    referrer = models.TextField(blank=True)
    load_time = models.FloatField(null=True)

    @property
    def duration(self):
        return self.last_seen - self.start_time
