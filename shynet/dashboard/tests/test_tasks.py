from django.core import mail
from django.test import TestCase

from dashboard.tasks import send_email


class SendEmailTests(TestCase):
    def test_sends_html_with_text_alternative(self):
        send_email(["a@example.com"], "Subject", "<p>Hello <b>world</b></p>")

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Subject")
        self.assertEqual(message.to, ["a@example.com"])
        self.assertIn("Hello", message.body)
        self.assertNotIn("<p>", message.body)
        self.assertEqual(message.alternatives[0][0], "<p>Hello <b>world</b></p>")
