from datetime import datetime, time

from django.utils import timezone


class DateRangeMixin:
    def get_start_date(self):
        if self.request.GET.get("startDate") is not None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("startDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.min))
        else:
            return timezone.now() - timezone.timedelta(days=30)

    def get_end_date(self):
        if self.request.GET.get("endDate") is not None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("endDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.max))
        else:
            return timezone.now()

    def get_date_ranges(self):
        now = timezone.now()
        return [
            {
                "name": "Last 3 days",
                "start": now - timezone.timedelta(days=2),
                "end": now,
            },
            {
                "name": "Last 30 days",
                "start": now - timezone.timedelta(days=29),
                "end": now,
            },
            {
                "name": "Last 90 days",
                "start": now - timezone.timedelta(days=89),
                "end": now,
            },
            {
                "name": "This month",
                "start": now.replace(day=1),
                "end": now,
            },
            {
                "name": "Last month",
                "start": (now.replace(day=1) - timezone.timedelta(days=1)).replace(
                    day=1
                ),
                "end": now.replace(day=1) - timezone.timedelta(days=1),
            },
            {
                "name": "This year",
                "start": now.replace(day=1, month=1),
                "end": now,
            },
        ]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["start_date"] = self.get_start_date()
        data["end_date"] = self.get_end_date()
        data["date_ranges"] = self.get_date_ranges()

        return data
