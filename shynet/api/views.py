from http import HTTPStatus

from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.views.generic import View

from core.models import Service
from core.utils import is_valid_uuid
from dashboard.mixins import DateRangeMixin
from .mixins import ApiTokenRequiredMixin


class DashboardApiView(ApiTokenRequiredMixin, DateRangeMixin, View):
    def get(self, request, *args, **kwargs):
        services = Service.objects.filter(Q(owner=request.user) | Q(collaborators__in=[request.user])).distinct()

        uuid_ = request.GET.get("uuid")
        if uuid_ and is_valid_uuid(uuid_):
            services = services.filter(uuid=uuid_)

        try:
            start = self.get_start_date()
            end = self.get_end_date()
        except ValueError:
            return JsonResponse(status=HTTPStatus.BAD_REQUEST, data={"error": "Invalid date format. Use YYYY-MM-DD."})

        service: Service
        services_data = [
            {
                "name": service.name,
                "uuid": service.uuid,
                "link": service.link,
                "stats": service.get_core_stats(start, end),
            }
            for service in services
        ]

        services_data = self._convert_querysets_to_lists(services_data)

        return JsonResponse(data={"services": services_data})

    def _convert_querysets_to_lists(self, services_data: list[dict]) -> list[dict]:
        for service_data in services_data:
            for key, value in service_data["stats"].items():
                if isinstance(value, QuerySet):
                    service_data["stats"][key] = list(value)
            for key, value in service_data["stats"]["compare"].items():
                if isinstance(value, QuerySet):
                    service_data["stats"]["compare"][key] = list(value)

        return services_data
