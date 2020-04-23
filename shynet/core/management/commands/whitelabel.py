from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site
from core.models import User
from django.utils.crypto import get_random_string
import uuid
import traceback


class Command(BaseCommand):
    help = "Configures a Shynet whitelabel"

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
        )

    def handle(self, *args, **options):
        site = Site.objects.get(pk=settings.SITE_ID)
        site.name = options.get("name")
        site.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully set the whitelabel to '{options.get('name')}'"
            )
        )