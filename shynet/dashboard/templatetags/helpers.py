from urllib.parse import urlparse

import flag
from django import template
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import SafeString

register = template.Library()


@register.filter
def naturaldelta(timedelta):
    if isinstance(timedelta, timezone.timedelta):
        seconds = timedelta.seconds
    else:
        seconds = timedelta
    string = ""
    if seconds // 3600 > 0:
        string += "{:02.0f}:".format(seconds // 3600)
    string += "{:02.0f}:".format((seconds % 3600) // 60)
    string += "{:02.0f}".format(seconds % 60)
    return string


@register.filter
def flag_emoji(isocode):
    try:
        return flag.flag(isocode)
    except:
        return ""


@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def urldisplay(url):
    if url.startswith("http"):
        display_url = url.replace("http://", "").replace("https://", "")
        return SafeString(
            f"<a href='{url}' title='{url}' rel='nofollow'>{escape(display_url if len(display_url) < 40 else display_url[:40] + '...')}</a>"
        )
    else:
        return url
