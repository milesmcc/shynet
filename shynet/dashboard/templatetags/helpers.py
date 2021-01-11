from urllib.parse import urlparse

import flag
import pycountry
from django import template
from django.conf import settings
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
def country_name(isocode):
    try:
        return pycountry.countries.get(alpha_2=isocode).name
    except:
        return "Unknown"


@register.simple_tag
def relative_stat_tone(
    start, end, good="UP", good_classes=None, bad_classes=None, neutral_classes=None,
):
    good_classes = good_classes or "~positive"
    bad_classes = bad_classes or "~critical"
    neutral_classes = neutral_classes or "~neutral"

    if start == None or end == None or start == end:
        return neutral_classes
    if good == "UP":
        return good_classes if start <= end else bad_classes
    elif good == "DOWN":
        return bad_classes if start <= end else good_classes
    else:
        return neutral_classes


@register.simple_tag
def percent_change_display(start, end):
    try:
        if start == None or end == None:
            return SafeString("&Delta; n/a")
        if start == end:
            direction = "&Delta; "
        else:
            direction = "&uarr; " if end > start else "&darr; "

        if start == 0 and end != 0:
            pct_change = "100%"
        elif start == 0:
            pct_change = "0%"
        else:
            change = int(round(100 * abs(end - start) / max(start, 1)))
            if change > 999:
                return "> 999%"
            else:
                pct_change = str(change) + "%"

        return SafeString(direction + pct_change)
    except: # TODO: filter for specific issues
        return SafeString("&Delta; ?")


@register.inclusion_tag("dashboard/includes/sidebar_footer.html")
def sidebar_footer():
    return {"version": settings.VERSION if settings.SHOW_SHYNET_VERSION else ""}


@register.inclusion_tag("dashboard/includes/stat_comparison.html")
def compare(
    start,
    end,
    good,
    classes="badge",
    good_classes=None,
    bad_classes=None,
    neutral_classes=None,
):
    return {
        "start": start,
        "end": end,
        "good": good,
        "classes": classes,
        "good_classes": good_classes,
        "bad_classes": bad_classes,
        "neutral_classes": neutral_classes,
    }


@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def iconify(text):
    if not settings.SHOW_THIRD_PARTY_ICONS:
        return ""

    text = text.lower()
    icons = {
        "chrome": "chrome.com",
        "safari": "www.apple.com",
        "windows": "windows.com",
        "edge": "microsoft.com",
        "firefox": "firefox.com",
        "opera": "opera.com",
        "unknown": "example.com",
        "linux": "kernel.org",
        "ios": "www.apple.com",
        "mac": "www.apple.com",
        "macos": "www.apple.com",
        "mac os x": "www.apple.com",
        "android": "android.com",
        "chrome os": "chrome.com",
        "ubuntu": "ubuntu.com",
        "fedora": "getfedora.org",
        "mobile safari": "www.apple.com",
        "chrome mobile ios": "chrome.com",
        "chrome mobile": "chrome.com",
        "samsung internet": "samsung.com",
        "google": "google.com",
        "chrome mobile webview": "chrome.com",
        "firefox mobile": "firefox.com",
        "edge mobile": "microsoft.com",
        "chromium": "chromium.org",
    }

    domain = None
    if text.startswith("http"):
        domain = urlparse(text).netloc
    elif text in icons:
        domain = icons[text]
    else:
        # This fallback works better than you'd think!
        domain = text + ".com"

    return SafeString(
        f'<span class="icon mr-1"><img src="https://icons.duckduckgo.com/ip3/{domain}.ico"></span>'
    )


@register.filter
def urldisplay(url):
    if url.startswith("http"):
        display_url = url.replace("http://", "").replace("https://", "")
        return SafeString(
            f"<a href='{url}' title='{url}' rel='nofollow' class='flex items-center'>{iconify(url)} {escape(display_url if len(display_url) < 40 else display_url[:40] + '...')}</a>"
        )
    else:
        return url
