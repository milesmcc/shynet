import uuid
from django.http import JsonResponse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import View

from dashboard.mixins import DateRangeMixin
from core.models import Service

from .mixins import ApiTokenRequiredMixin


def is_valid_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class DashboardApiView(ApiTokenRequiredMixin, DateRangeMixin, View):
    def get(self, request, *args, **kwargs):
        services = Service.objects.filter(
            Q(owner=request.user) | Q(collaborators__in=[request.user])
        ).distinct()

        uuid = request.GET.get("uuid")
        if uuid and is_valid_uuid(uuid):
            services = services.filter(uuid=uuid)

        try:
            start = self.get_start_date()
            end = self.get_end_date()
        except ValueError:
            return JsonResponse(status=400, data={"error": "Invalid date format"})

        services_data = [
            {
                "name": s.name,
                "uuid": s.uuid,
                "link": s.link,
                "stats": s.get_core_stats(start, end),
            }
            for s in services
        ]

        services_data = self._convert_querysets_to_lists(services_data)

        return JsonResponse(data={"services": services_data})

    def _convert_querysets_to_lists(self, services_data):
        for service_data in services_data:
            for key, value in service_data["stats"].items():
                if isinstance(value, QuerySet):
                    service_data["stats"][key] = list(value)
            for key, value in service_data["stats"]["compare"].items():
                if isinstance(value, QuerySet):
                    service_data["stats"]["compare"][key] = list(value)

        return services_data
