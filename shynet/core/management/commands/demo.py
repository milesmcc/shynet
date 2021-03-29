import traceback
from django.utils.timezone import now
from django.utils.timezone import timedelta
import random
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string
import user_agents
from logging import info

from core.models import User, Service
from analytics.models import Session, Hit
from analytics.tasks import ingress_request

LOCATIONS = [
    "/",
    "/post/{rand}",
    "/login",
    "/me",
]

REFERRERS = [
    "https://news.ycombinator.com/item?id=11116274",
    "https://news.ycombinator.com/item?id=24872911",
    "https://reddit.com",
    "https://facebook.com",
    "https://twitter.com/milesmccain",
    "https://twitter.com",
    "https://stanford.edu/~mccain/",
    "https://tiktok.com",
    "https://io.stanford.edu",
    "https://en.wikipedia.org",
    "https://stackoverflow.com",
    "",
    "",
    "",
    "",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/43.4",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko)",
    "Version/10.0 Mobile/14E304 Safari/602.1",
]


class Command(BaseCommand):
    help = "Configures a Shynet demo service"

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
        )
        parser.add_argument("owner_email", type=str)
        parser.add_argument(
            "avg",
            type=int,
        )
        parser.add_argument("deviation", type=float, default=0.4)
        parser.add_argument(
            "days",
            type=int,
        )
        parser.add_argument("load_time", type=float, default=1000)

    def handle(self, *args, **options):
        owner = User.objects.get(email=options.get("owner_email"))
        service = Service.objects.create(name=options.get("name"), owner=owner)

        print(
            f"Created demo service `{service.name}` (uuid: `{service.uuid}`, owner: {owner})"
        )

        # Go through each day requested, creating sessions and hits
        for days in range(options.get("days")):
            day = (now() - timedelta(days=days)).replace(hour=0, minute=0, second=0)
            print(f"Populating info for {day}...")
            avg = options.get("avg")
            deviation = options.get("deviation")
            ips = [
                ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
                for _ in range(avg)
            ]

            n = avg + random.randrange(-1 * deviation * avg, deviation * avg)
            for _ in range(n):
                time = day + timedelta(
                    hours=random.randrange(0, 23),
                    minutes=random.randrange(0, 59),
                    seconds=random.randrange(0, 59),
                )
                ip = random.choice(ips)
                load_time = random.normalvariate(options.get("load_time"), 500)
                referrer = random.choice(REFERRERS)
                location = "https://example.com" + random.choice(LOCATIONS).replace(
                    "{rand}", str(random.randint(0, n))
                )
                user_agent = random.choice(USER_AGENTS)
                ingress_request(
                    service.uuid,
                    "JS",
                    time,
                    {"loadTime": load_time, "referrer": referrer},
                    ip,
                    location,
                    user_agent,
                )

            print(f"Created {n} demo hits on {day}!")

        self.stdout.write(self.style.SUCCESS(f"Successfully created demo data!"))
