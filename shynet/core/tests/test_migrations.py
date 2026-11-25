from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class MigrationTests(TestCase):
    def test_no_model_changes_without_migration(self):
        out = StringIO()
        try:
            call_command(
                "makemigrations", "core", "analytics", check=True, dry_run=True, stdout=out
            )
        except SystemExit:
            self.fail(f"Model changes are missing a migration:\n{out.getvalue()}")
