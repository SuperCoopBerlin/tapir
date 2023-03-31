from django import template
from django.template.defaultfilters import stringfilter

from tapir.configuration.parameter import get_parameter_value

register = template.Library()


@register.filter(name="parameter")
@stringfilter
def parameter_value(key: str):
    return get_parameter_value(key)
