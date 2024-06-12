import datetime

from django import template

register = template.Library()


@register.filter
def negative_deactivated(value: datetime.timedelta):
    if value < datetime.timedelta(0):
        return "deactivated"
    else:
        return value
