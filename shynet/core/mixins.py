from urllib.parse import urlparse

from django.utils import timezone


class DateRangeMixin:
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if self.request.GET.get("startDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("startDate"), "%Y-%m-%d"
            )
            found_time.replace(hour=0, minute=0)
            data["start_date"] = found_time
        else:
            data["start_date"] = timezone.now() - timezone.timedelta(days=30)

        if self.request.GET.get("endDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("endDate"), "%Y-%m-%d"
            )
            found_time.replace(hour=23, minute=59)
            data["end_date"] = found_time
        else:
            data["end_date"] = timezone.now()

        return data


class BaseUrlMixin:
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        url_data = urlparse(self.request.build_absolute_uri())
        data["base_url"] = f"{url_data.scheme}://{url_data.netloc}"
        return data
