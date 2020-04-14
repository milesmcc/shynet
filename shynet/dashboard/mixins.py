from urllib.parse import urlparse

from django.utils import timezone


class DateRangeMixin:
    def get_start_date(self):
        if self.request.GET.get("startDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("startDate"), "%Y-%m-%d"
            )
            found_time.replace(hour=0, minute=0)
            return found_time
        else:
            return timezone.now() - timezone.timedelta(days=30)

    def get_end_date(self):
        if self.request.GET.get("endDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("endDate"), "%Y-%m-%d"
            )
            found_time.replace(hour=23, minute=59)
            return found_time
        else:
            return timezone.now()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["start_date"] = self.get_start_date()
        data["end_date"] = self.get_end_date()
        return data


class BaseUrlMixin:
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        url_data = urlparse(self.request.build_absolute_uri())
        data["base_url"] = f"{url_data.scheme}://{url_data.netloc}"
        return data
