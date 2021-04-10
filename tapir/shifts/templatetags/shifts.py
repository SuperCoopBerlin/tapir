from builtins import enumerate

from django import template
from django.urls import reverse

from tapir.shifts.models import (
    Shift,
    ShiftTemplate,
    ShiftAttendanceTemplate,
    WEEKDAY_CHOICES,
)

register = template.Library()


@register.inclusion_tag("shifts/shift_block_tag.html", takes_context=True)
def shift_block(context, shift: Shift):
    context["shift"] = shift_to_block_object(shift)
    return context


@register.inclusion_tag("shifts/shift_block_tag.html", takes_context=True)
def shift_template_block(context, shift_template: ShiftTemplate):
    context["shift"] = shift_template_to_block_object(shift_template)
    return context


def shift_to_block_object(shift: Shift):
    attendances = ["empty" for _ in range(shift.num_slots)]
    for index, attendance in enumerate(shift.get_valid_attendances()):
        attendances[index] = "single"
        if (
            shift.shift_template is not None
            and ShiftAttendanceTemplate.objects.filter(
                shift_template=shift.shift_template, user=attendance.user
            ).count()
            > 0
        ):
            attendances[index] = "template"

    template_group = None
    if shift.shift_template is not None:
        template_group = template_group_name_to_character(
            shift.shift_template.group.name
        )

    background = "success"
    if shift.get_valid_attendances() == 0:
        background = "danger"
    elif shift.get_valid_attendances().count() < shift.num_slots:
        background = "warning"

    return {
        "url": shift.get_absolute_url(),
        "attendances": attendances,
        "name": shift.name,
        "num_slots": shift.num_slots,
        "start_time": shift.start_time,
        "end_time": shift.end_time,
        "start_date": shift.start_time,
        "weekday": None,
        "template_group": template_group,
        "background": background,
    }


def shift_template_to_block_object(shift_template: ShiftTemplate):
    attendances = ["empty" for _ in range(shift_template.num_slots)]
    attendance_templates = ShiftAttendanceTemplate.objects.filter(
        shift_template=shift_template
    )
    for index in range(attendance_templates.count()):
        attendances[index] = "template"

    background = "success"
    if attendance_templates.count() == 0:
        background = "danger"
    elif attendance_templates.count() < shift_template.num_slots:
        background = "warning"

    return {
        "url": reverse("admin:shifts_shifttemplate_change", args=[shift_template.pk]),
        "attendances": attendances,
        "name": shift_template.name,
        "num_slots": shift_template.num_slots,
        "start_time": shift_template.start_time,
        "end_time": shift_template.end_time,
        "start_date": None,
        "weekday": WEEKDAY_CHOICES[shift_template.weekday][1],
        "template_group": template_group_name_to_character(shift_template.group.name),
        "background": background,
    }


def template_group_name_to_character(name: str):
    if name[-1] == "A":
        return "Ⓐ"
    if name[-1] == "B":
        return "Ⓑ"
    if name[-1] == "C":
        return "Ⓒ"
    if name[-1] == "D":
        return "Ⓓ"
    return None
