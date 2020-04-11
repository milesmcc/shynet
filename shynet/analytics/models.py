import json
import uuid

from django.db import models

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
    os = models.TextField()
    ip = models.GenericIPAddressField()

    # GeoIP data
    asn = models.TextField(blank=True)
    country = models.TextField(blank=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    time_zone = models.TextField(blank=True)


class Hit(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    # Base request information
    start_time = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)
    heartbeats = models.IntegerField(default=0)
    tracker = models.TextField()  # Tracking pixel or JS

    # Advanced page information
    location = models.TextField(blank=True)
    referrer = models.TextField(blank=True)
    loadTime = models.FloatField(null=True)
    httpStatus = models.IntegerField(null=True)
    