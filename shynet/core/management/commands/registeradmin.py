import traceback
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from core.models import User


class Command(BaseCommand):
    help = "Creates an admin user with an auto-generated password"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
        )

    def handle(self, *args, **options):
        email = options.get("email")
        password = get_random_string(10)
        User.objects.create_superuser(str(uuid.uuid4()), email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Successfully created a Shynet superuser"))
        self.stdout.write(f"Email address: {email}")
        self.stdout.write(f"Password: {password}")
