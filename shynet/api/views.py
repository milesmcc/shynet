from django.http import JsonResponse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import View

from dashboard.mixins import DateRangeMixin
from core.models import Service

from .mixins import ApiTokenRequiredMixin


class DashboardApiView(ApiTokenRequiredMixin, DateRangeMixin, View):
    def get(self, request, *args, **kwargs):
        services = Service.objects.filter(
            Q(owner=request.user) | Q(collaborators__in=[request.user])
        ).distinct()

        start = self.get_start_date()
        end = self.get_end_date()
        services_data = [s.get_core_stats(start, end) for s in services]
        for service_data in services_data:
            for key, value in service_data.items():
                if isinstance(value, QuerySet):
                    service_data[key] = list(value)
            for key, value in service_data['compare'].items():
                if isinstance(value, QuerySet):
                    service_data['compare'][key] = list(value)

        return JsonResponse(data={'services': services_data})
