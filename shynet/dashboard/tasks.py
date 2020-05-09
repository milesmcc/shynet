from celery import shared_task
from django.core import mail
from django.conf import settings
import html2text


@shared_task
def send_email(to: [str], subject: str, content: str, from_email: str = None):
    text_content = html2text.html2text(content)
    mail.send_mail(
        subject,
        text_content,
        from_email or settings.DEFAULT_FROM_EMAIL,
        to,
        html_message=content,
    )
