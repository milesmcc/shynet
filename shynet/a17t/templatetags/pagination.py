# From https://djangosnippets.org/snippets/1441/

from django import template
from django.utils.http import urlencode

register = template.Library()


@register.inclusion_tag("a17t/includes/pagination.html")
def pagination(
    page,
    request,
    begin_pages=2,
    end_pages=2,
    before_current_pages=4,
    after_current_pages=4,
):
    url_parameters = urlencode(
        [(key, value) for key, value in request.GET.items() if key != "page"]
    )

    before = max(page.number - before_current_pages - 1, 0)
    after = page.number + after_current_pages

    begin = page.paginator.page_range[:begin_pages]
    middle = page.paginator.page_range[before:after]
    end = page.paginator.page_range[-end_pages:]
    last_page_number = end[-1]

    def collides(firstlist, secondlist):
        return any(item in secondlist for item in firstlist)

    if collides(middle, end):
        end = range(max(page.number - before_current_pages, 1), last_page_number + 1)
        middle = []

    if collides(begin, middle):
        begin = range(1, min(page.number + after_current_pages, last_page_number) + 1)
        middle = []

    if collides(begin, end):
        begin = range(1, last_page_number + 1)
        end = []

    return {
        "page": page,
        "begin": begin,
        "middle": middle,
        "end": end,
        "url_parameters": url_parameters,
    }
