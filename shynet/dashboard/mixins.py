from datetime import datetime, time
from urllib.parse import urlparse

from django.utils import timezone


class DateRangeMixin:
    def get_start_date(self, use_default=True):
        if self.request.GET.get("startDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("startDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.min))
        elif use_default == True:
            return timezone.now() - timezone.timedelta(days=30)
        else:
            return None

    def get_end_date(self):
        if self.request.GET.get("endDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("endDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.max))
        else:
            return timezone.now()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["start_date"] = self.get_start_date()
        data["end_date"] = self.get_end_date()
        start_date = self.get_start_date(False)
        data["date_query_params"] = f"?startDate={start_date.strftime('%Y-%m-%d')}&endDate={self.get_end_date().strftime('%Y-%m-%d')}" if start_date is not None else ""
        return data
