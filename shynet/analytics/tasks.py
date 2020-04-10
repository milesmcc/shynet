import json
import logging

import geoip2.database
import user_agents
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.models import Service

from .models import Hit, Session

log = logging.getLogger(__name__)

_geoip2_city_reader = None
_geoip2_asn_reader = None


def _geoip2_lookup(ip):
    global _geoip2_city_reader, _geoip2_asn_reader  # TODO: is there a better way to do global Django vars? Is this thread safe?
    try:
        if settings.MAXMIND_CITY_DB == None or settings.MAXMIND_ASN_DB == None:
            return None
        if _geoip2_city_reader == None or _geoip2_asn_reader == None:
            _geoip2_city_reader = geoip2.database.Reader(settings.MAXMIND_CITY_DB)
            _geoip2_asn_reader = geoip2.database.Reader(settings.MAXMIND_ASN_DB)
        city_results = _geoip2_city_reader.city(ip)
        asn_results = _geoip2_asn_reader.asn(ip)
        return {
            "asn": asn_results.autonomous_system_organization,
            "country": city_results.country.iso_code,
            "longitude": city_results.location.longitude,
            "latitude": city_results.location.latitude,
            "time_zone": city_results.location.time_zone,
        }
    except geoip2.errors.AddressNotFoundError:
        return {}


@shared_task
def ingress_request(
    service_uuid, tracker, time, payload, ip, location, user_agent, identifier=""
):
    try:
        ip_data = _geoip2_lookup(ip)

        service = Service.objects.get(uuid=service_uuid)
        log.debug(f"Linked to service {service}")

        # Create or update session
        session_metadata = payload.get("sessionMetadata", {})
        session = Session.objects.filter(
            service=service,
            last_seen__gt=timezone.now() - timezone.timedelta(minutes=30),
            ip=ip,
            user_agent=user_agent,
            identifier=identifier,
        ).first()
        if session is None:
            log.debug("Cannot link to existing session; creating a new one...")
            ua = user_agents.parse(user_agent)

            session = Session.objects.create(
                service=service,
                ip=ip,
                user_agent=user_agent,
                identifier=identifier,
                browser=f"{ua.browser.family or ''} {ua.browser.version_string or ''}".strip(),
                device=f"{ua.device.model or ''}",
                os=f"{ua.os.family or ''} {ua.os.version_string or ''}".strip(),
                metadata_raw=json.dumps(session_metadata),
                asn=ip_data.get("asn", ""),
                country=ip_data.get("country", ""),
                longitude=ip_data.get("longitude"),
                latitude=ip_data.get("latitude"),
                time_zone=ip_data.get("time_zone", ""),
            )
        else:
            log.debug("Updating old session with new data...")
            # Update old metadata with new metadata
            new_metadata = session.metadata
            new_metadata.update(session_metadata)
            session.metadata_raw = json.dumps(new_metadata)
            # Update last seen time
            session.last_seen = timezone.now()
            session.save()

        # Create or update hit
        hit_metadata = payload.get("hitMetadata", {})
        idempotency = payload.get("idempotency")
        idempotency_path = f"hit_idempotency_{idempotency}"
        hit = None
        if idempotency is not None:
            if cache.get(idempotency_path) is not None:
                hit = Hit.objects.filter(
                    pk=cache.get(idempotency_path), session=session
                ).first()
                if hit is not None:
                    # There is an existing hit with an identical idempotency key. That means
                    # this is a heartbeat.
                    log.debug("Hit is a heartbeat; updating old hit with new data...")
                    hit.heartbeats += 1
                    hit.duration = (timezone.now() - hit.start).total_seconds()
                    new_metadata = hit.metadata
                    new_metadata.update(hit_metadata)
                    hit.metadata_raw = json.dumps(new_metadata)
                    hit.save()
        if hit is None:
            log.debug("Hit is a page load; creating new hit...")
            # There is no existing hit; create a new one
            hit = Hit.objects.create(
                session=session,
                tracker=tracker,
                location=location,
                referrer=payload.get("referrer", ""),
                loadTime=payload.get("loadTime"),
                metadata_raw=json.dumps(hit_metadata),
            )
            # Set idempotency (if applicable)
            if idempotency is not None:
                cache.set(idempotency_path, hit.pk, timeout=30 * 60)
    except Exception as e:
        log.error(e)
