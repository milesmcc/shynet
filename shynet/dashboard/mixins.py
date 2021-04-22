import json

from datetime import datetime, time
from urllib.parse import urlparse

from django.utils import timezone


class DateRangeMixin:
    def get_start_date(self):
        if self.request.GET.get("startDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("startDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.min))
        else:
            return timezone.now() - timezone.timedelta(days=30)

    def get_end_date(self):
        if self.request.GET.get("endDate") != None:
            found_time = timezone.datetime.strptime(
                self.request.GET.get("endDate"), "%Y-%m-%d"
            )
            return timezone.make_aware(datetime.combine(found_time, time.max))
        else:
            return timezone.now()

    def get_date_ranges(self):
        now = timezone.now()
        return [
            {'name': 'Today', 'start': now, 'end': now},
            {
                'name': 'Yesterday',
                'start': now - timezone.timedelta(days=1),
                'end': now - timezone.timedelta(days=1),
            },
            {
                'name': 'Last 7 days',
                'start': now - timezone.timedelta(days=7),
                'end': now,
            },
            {
                'name': 'Last 30 days',
                'start': now - timezone.timedelta(days=30),
                'end': now,
            },
            {
                'name': 'Last 90 days',
                'start': now - timezone.timedelta(days=90),
                'end': now,
            },
            {
                'name': 'This month',
                'start': now.replace(day=1),
                'end': now,
            },
            {
                'name': 'Last month',
                'start': now.replace(day=1, month=now.month - 1),
                'end': now.replace(day=1, month=now.month) - timezone.timedelta(days=1),
            },
            {
                'name': 'This year',
                'start': now.replace(day=1, month=1),
                'end': now,
            },
            {
                'name': 'Last year',
                'start': now.replace(day=1, month=1, year=now.year - 1),
                'end': now.replace(day=1, month=1) - timezone.timedelta(days=1),
            },
        ]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["start_date"] = self.get_start_date()
        data["end_date"] = self.get_end_date()
        data["date_ranges"] = self.get_date_ranges()

        return data
