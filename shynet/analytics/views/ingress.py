import base64
import json
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import render, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from ipware import get_client_ip

from core.models import Service

from ..tasks import ingress_request


def ingress(request, service_uuid, identifier, tracker, payload):
    time = timezone.now()
    client_ip, is_routable = get_client_ip(request)
    location = request.META.get("HTTP_REFERER", "").strip()
    user_agent = request.META.get("HTTP_USER_AGENT", "").strip()
    dnt = request.META.get("HTTP_DNT", "0").strip() == "1"
    gpc = request.META.get("HTTP_SEC_GPC", "0").strip() == "1"
    if gpc or dnt:
        dnt = True

    ingress_request.delay(
        service_uuid,
        tracker,
        time,
        payload,
        client_ip,
        location,
        user_agent,
        dnt=dnt,
        identifier=identifier,
    )


class ValidateServiceOriginsMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            service_uuid = self.kwargs.get("service_uuid")
            origins = cache.get(f"service_origins_{service_uuid}")

            if origins is None:
                service = Service.objects.get(uuid=service_uuid)
                origins = service.origins
                cache.set(f"service_origins_{service_uuid}", origins, timeout=3600)

            allow_origin = "*"

            if origins != "*":
                remote_origin = request.META.get("HTTP_ORIGIN")
                if (
                    remote_origin is None
                    and request.META.get("HTTP_REFERER") is not None
                ):
                    parsed = urlparse(request.META.get("HTTP_REFERER"))
                    remote_origin = f"{parsed.scheme}://{parsed.netloc}".lower()
                origins = [origin.strip().lower() for origin in origins.split(",")]
                if remote_origin in origins:
                    allow_origin = remote_origin
                else:
                    return HttpResponseForbidden()

            resp = super().dispatch(request, *args, **kwargs)
            resp["Access-Control-Allow-Origin"] = allow_origin
            resp["Access-Control-Allow-Methods"] = "GET,HEAD,OPTIONS,POST"
            resp[
                "Access-Control-Allow-Headers"
            ] = "Origin, X-Requested-With, Content-Type, Accept, Authorization, Referer"
            return resp
        except Service.DoesNotExist:
            raise Http404()
        except ValidationError:
            return HttpResponseBadRequest()


class PixelView(ValidateServiceOriginsMixin, View):
    # Fallback view to serve an unobtrusive 1x1 transparent tracking pixel for browsers with
    # JavaScript disabled.
    def get(self, *args, **kwargs):
        # Extract primary data
        ingress(
            self.request,
            self.kwargs.get("service_uuid"),
            self.kwargs.get("identifier", ""),
            "PIXEL",
            {},
        )

        data = base64.b64decode(
            "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
        )
        resp = HttpResponse(data, content_type="image/gif")
        resp["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp["Access-Control-Allow-Origin"] = "*"
        return resp


@method_decorator(csrf_exempt, name="dispatch")
class ScriptView(ValidateServiceOriginsMixin, View):
    def get(self, *args, **kwargs):
        protocol = "https" if settings.SCRIPT_USE_HTTPS else "http"
        endpoint = (
            reverse(
                "ingress:endpoint_script",
                kwargs={
                    "service_uuid": self.kwargs.get("service_uuid"),
                },
            )
            if self.kwargs.get("identifier") is None
            else reverse(
                "ingress:endpoint_script_id",
                kwargs={
                    "service_uuid": self.kwargs.get("service_uuid"),
                    "identifier": self.kwargs.get("identifier"),
                },
            )
        )
        heartbeat_frequency = settings.SCRIPT_HEARTBEAT_FREQUENCY
        dnt = self.request.META.get("HTTP_DNT", "0").strip() == "1"
        service_uuid = self.kwargs.get("service_uuid")
        service = Service.objects.get(pk=service_uuid, status=Service.ACTIVE)
        response = render(
            self.request,
            "analytics/scripts/page.js",
            context=dict(
                {
                    "endpoint": endpoint,
                    "protocol": protocol,
                    "heartbeat_frequency": heartbeat_frequency,
                    "script_inject": self.get_script_inject(),
                    "dnt": dnt and service.respect_dnt,
                }
            ),
            content_type="application/javascript",
        )

        response["Cache-Control"] = "public, max-age=31536000"  # 1 year
        return response

    def post(self, *args, **kwargs):
        payload = json.loads(self.request.body)
        ingress(
            self.request,
            self.kwargs.get("service_uuid"),
            self.kwargs.get("identifier", ""),
            "JS",
            payload,
        )
        return HttpResponse(
            json.dumps({"status": "OK"}), content_type="application/json"
        )

    def get_script_inject(self):
        service_uuid = self.kwargs.get("service_uuid")
        script_inject = cache.get(f"script_inject_{service_uuid}")
        if script_inject is None:
            service = Service.objects.get(uuid=service_uuid)
            script_inject = service.script_inject
            cache.set(f"script_inject_{service_uuid}", script_inject, timeout=3600)
        return script_inject
