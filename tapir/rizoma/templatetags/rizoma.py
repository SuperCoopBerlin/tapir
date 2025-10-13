from django import template
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.formats import date_format
from django.utils import timezone

register = template.Library()

@register.simple_tag()
def rizoma_photo_url(photo_id: str) -> str:
    return f"{settings.COOPS_PT_API_BASE_URL}/files/memberPhotos/{photo_id}-thumb.jpg"

@register.simple_tag
def format_shift_date(shift):
    display_name = "%s" % (
        date_format(timezone.localtime(shift.start_time)),
    )
    if shift.shift_template and shift.shift_template.group:
        display_name = f"{display_name} ({shift.shift_template.group.name})"

    return display_name

@register.simple_tag
def format_shift_time(shift):
    display_name = "%s - %s" % (
        timezone.localtime(shift.start_time).strftime("%Hh%M"),
        timezone.localtime(shift.end_time).strftime("%Hh%M"),
    )

    return display_name


@register.simple_tag
def format_shift_template_date(shift_template):
    display_name = "%s" % (
        _(shift_template.get_weekday_display())
    )
    if shift_template.group:
            display_name = f"{display_name} ({shift_template.group.name})"

    return display_name

@register.simple_tag
def format_shift_template_time(shift_template):
    display_name = "%s" % (
        shift_template.start_time.strftime("%Hh%M"),
    )
    return display_name

@register.simple_tag
def format_shift_slot_name(shift_slot):
    display_name = "%s %s" % (
        shift_slot.shift.name,
        shift_slot.name,
    )

    return display_name