import uuid

from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Service, ACTIVE_USER_TIMEDELTA


def _default_uuid():
    return str(uuid.uuid4())


class Session(models.Model):
    uuid = models.UUIDField(default=_default_uuid, primary_key=True)
    service = models.ForeignKey(
        Service, verbose_name=_("Service"), on_delete=models.CASCADE, db_index=True
    )

    # Cross-session identification; optional, and provided by the service
    identifier = models.TextField(
        blank=True, db_index=True, verbose_name=_("Identifier")
    )

    # Time
    start_time = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name=_("Start time")
    )
    last_seen = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name=_("Last seen")
    )

    # Core request information
    user_agent = models.TextField(verbose_name=_("User agent"))
    browser = models.TextField(verbose_name=_("Browser"))
    device = models.TextField(verbose_name=_("Device"))
    device_type = models.CharField(
        max_length=7,
        choices=[
            ("PHONE", _("Phone")),
            ("TABLET", _("Tablet")),
            ("DESKTOP", _("Desktop")),
            ("ROBOT", _("Robot")),
            ("OTHER", _("Other")),
        ],
        default="OTHER",
        verbose_name=_("Device type"),
    )
    os = models.TextField(verbose_name=_("OS"))
    ip = models.GenericIPAddressField(db_index=True, null=True, verbose_name=_("IP"))

    # GeoIP data
    asn = models.TextField(blank=True, verbose_name=_("Asn"))
    country = models.TextField(blank=True, verbose_name=_("Country"))
    longitude = models.FloatField(null=True, verbose_name=_("Longitude"))
    latitude = models.FloatField(null=True, verbose_name=_("Latitude"))
    time_zone = models.TextField(blank=True, verbose_name=_("Time zone"))

    is_bounce = models.BooleanField(
        default=True, db_index=True, verbose_name=_("Is bounce")
    )

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
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
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, db_index=True, verbose_name=_("Session")
    )
    initial = models.BooleanField(default=True, db_index=True)

    # Base request information
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    heartbeats = models.IntegerField(default=0)
    tracker = models.TextField(
        choices=[("JS", "JavaScript"), ("PIXEL", "Pixel (noscript)")]
    )  # Tracking pixel or JS

    # Advanced page information
    location = models.TextField(blank=True, db_index=True)
    referrer = models.TextField(blank=True, db_index=True)
    load_time = models.FloatField(null=True, db_index=True)

    # While not necessary, we store the root service directly for performance.
    # It makes querying much easier; no need for inner joins.
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_index=True)

    class Meta:
        verbose_name = _("Hit")
        verbose_name_plural = _("Hits")
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
