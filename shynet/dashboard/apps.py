from django.apps import AppConfig
from django.conf import settings


class DashboardConfig(AppConfig):
    name = "dashboard"

    def ready(self):
        if not settings.ACCOUNT_SIGNUPS_ENABLED:
            # Normally you'd do this in settings.py, but this must be done _after_ apps are enabled
            from allauth.account.adapter import DefaultAccountAdapter

            DefaultAccountAdapter.is_open_for_signup = lambda k, v: False
