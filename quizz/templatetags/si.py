from django import template
from django.utils.safestring import mark_safe
from si_prefix import split, prefix

register = template.Library()


@register.filter
def si(value, wrap_span_class=None):
    base, exp = split(int(value), precision=1)
    prefix_unit = ""

    if exp:
        prefix_unit = prefix(exp)

        if wrap_span_class:
            prefix_unit = f'<span class="{wrap_span_class}">{prefix_unit}</span>'

    if base == int(base):
        return mark_safe(f"{base:.0f}{prefix_unit}")
    else:
        return mark_safe(f"{base:.1f}{prefix_unit}")
