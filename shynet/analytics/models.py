import uuid

from django.db import models
from django.shortcuts import reverse
from django.utils import timezone

from core.models import Service, ACTIVE_USER_TIMEDELTA


def _default_uuid():
    return str(uuid.uuid4())


class Session(models.Model):
    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_index=True)

    # Cross-session identification; optional, and provided by the service
    identifier = models.TextField(blank=True, db_index=True)

    # Time
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)

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

    is_bounce = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["service", "-start_time"]),
            models.Index(fields=["service", "-last_seen"]),
            models.Index(fields=["service", "identifier"]),
        ]

    @property
    def is_currently_active(self):
        return timezone.now() - self.last_seen < ACTIVE_USER_TIMEDELTA

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

    def recalculate_bounce(self):
        bounce = self.hit_set.count() == 1
        if bounce != self.is_bounce:
            self.is_bounce = bounce
            self.save()


class Hit(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, db_index=True)

    type = models.TextField(
        choices=[("visit", "Visit"), ("event", "Event")],
        default="visit"
    )  # Tracking pixel or JS

    # Base request information
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)

    # TODO: rename heartbeats field so it can be used to count events,
    # as well as page heartbeats
    heartbeats = models.IntegerField(default=0)

    # Advanced page information
    location = models.TextField(blank=True, db_index=True)

    # -- Visit specific Fields
    initial = models.BooleanField(default=True, db_index=True)
    tracker = models.TextField(
        choices=[("JS", "JavaScript"), ("PIXEL", "Pixel (noscript)")]
    )  # Tracking pixel or JS
    load_time = models.FloatField(null=True, db_index=True)
    referrer = models.TextField(blank=True, db_index=True)

    # -- Event specific fields
    event = models.ForeignKey(
        'EventListener', on_delete=models.CASCADE,
        db_index=True,
        null=True
    )

    # While not necessary, we store the root service directly for performance.
    # It makes querying much easier; no need for inner joins.
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_index=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["session", "-start_time"]),
            models.Index(fields=["service", "-start_time"]),
            models.Index(fields=["session", "location"]),
            models.Index(fields=["session", "referrer"]),
        ]

    @property
    def duration(self):
        return self.last_seen - self.start_time

    def get_absolute_url(self):
        return reverse(
            "dashboard:service_session",
            kwargs={"pk": self.service.pk, "session_pk": self.session.pk},
        )


class EventListener(models.Model):
    """
    An EventListener is type of event (eg. button-click) to attach
    to elements to the page. We can chose to accept all kinds of events
    or pre-create the events and reject any event that is not pre-created
    """
    name = models.TextField(blank=False, db_index=True)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        db_index=True
    )
