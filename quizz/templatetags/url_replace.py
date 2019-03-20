from urllib.parse import urlencode
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    request = None
    if "request" in context:
        request = context["request"]
    else:
        for ctx in context:
            if "request" in ctx:
                request = ctx["request"]
                break

    if not request:
        return urlencode(kwargs)

    query = request.GET.dict()
    query.update(kwargs)

    return urlencode(query)
