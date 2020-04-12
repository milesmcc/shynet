import flag
from django import template
from django.utils import timezone

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
