from datetime import timedelta, date, datetime, time

from django import template
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tapir.shifts.models import (
    Shift,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftAttendance,
    ShiftTemplateGroup,
)
from tapir.utils.shortcuts import get_monday

register = template.Library()


@register.inclusion_tag("shifts/user_shifts_overview_tag.html", takes_context=True)
def user_shifts_overview(context, user):
    context["user"] = user
    return context


@register.inclusion_tag("shifts/shift_block_tag.html", takes_context=True)
def shift_block(context, shift: Shift, fill_parent=False):
    context["shift"] = shift_to_block_object(shift, fill_parent)
    return context


@register.inclusion_tag("shifts/shift_block_tag.html", takes_context=True)
def shift_template_block(context, shift_template: ShiftTemplate, fill_parent=False):
    context["shift"] = shift_template_to_block_object(shift_template, fill_parent)
    return context


def shift_name_as_class(shift_name: str) -> str:
    return shift_name.replace(" ", "_").lower()


def shift_to_block_object(shift: Shift, fill_parent: bool):
    attendances = {}

    filter_classes = set()

    num_valid_attendances = 0

    for slot in shift.slots.all():
        slot_name = slot.name
        if slot_name == "":
            slot_name = _("General")
        if slot_name not in attendances:
            attendances[slot_name] = []

        attendance = None
        for a in slot.attendances.all():
            if a.is_valid():
                attendance = a
                break

        if attendance:
            num_valid_attendances += 1

        if attendance:
            if attendance.state == ShiftAttendance.State.LOOKING_FOR_STAND_IN:
                filter_classes.add("freeslot_any")
                filter_classes.add("freeslot_" + shift_name_as_class(slot.name))

                state = "standin"
            elif (
                slot.slot_template is not None
                and hasattr(slot.slot_template, "attendance_template")
                and slot.slot_template.attendance_template.user == attendance.user
            ):
                state = "regular"
            else:
                state = "single"
        else:
            filter_classes.add("freeslot_any")
            filter_classes.add("freeslot_" + shift_name_as_class(slot.name))
            state = "empty"

        attendances[slot_name].append(state)

    if num_valid_attendances < shift.get_num_required_attendances():
        filter_classes.add("needs_help")

    template_group = None
    if shift.shift_template:
        template_group = template_group_name_to_character(
            shift.shift_template.group.name
        )

    style = ""
    if fill_parent:
        style = "height:100%; width: 100%;"

    return {
        "attendances": attendances,
        "name": shift.name,
        "start_time": shift.start_time,
        "end_time": shift.end_time,
        "start_date": shift.start_time,
        "weekday": None,
        "template_group": template_group,
        "style": style,
        "id": shift.id,
        "is_template": False,
        "filter_classes": filter_classes,
    }


def shift_template_to_block_object(shift_template: ShiftTemplate, fill_parent: bool):
    attendances = {}

    filter_classes = set()

    num_attendances = 0

    for slot_template in shift_template.slot_templates.all():
        slot_name = slot_template.name
        if slot_template.name == "":
            slot_name = _("General")
        if slot_name not in attendances:
            attendances[slot_name] = []

        if slot_template.get_attendance_template():
            state = "regular"
            num_attendances += 1
        else:
            state = "empty"
            filter_classes.add("freeslot_any")
            filter_classes.add("freeslot_" + shift_name_as_class(slot_template.name))

        attendances[slot_name].append(state)

    if num_attendances < shift_template.num_required_attendances:
        filter_classes.add("needs_help")

    style = ""
    if fill_parent:
        style = "height:100%; width: 100%;"

    return {
        "attendances": attendances,
        "name": shift_template.name,
        "start_time": shift_template.start_time,
        "end_time": shift_template.end_time,
        "start_date": None,
        "weekday": WEEKDAY_CHOICES[shift_template.weekday][1],
        "template_group": template_group_name_to_character(shift_template.group.name),
        "style": style,
        "id": shift_template.id,
        "is_template": True,
        "filter_classes": filter_classes,
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


@register.inclusion_tag("shifts/shift_filters.html", takes_context=True)
def shift_filters(context):
    return context


@register.simple_tag
def get_week_group(target_time: date) -> ShiftTemplateGroup | None:
    for delta in list(range(52)) + list(range(-52, 0)):
        monday = get_monday(target_time) + timedelta(weeks=delta)
        monday = datetime.combine(monday, time(), timezone.now().tzinfo)
        sunday = monday + timedelta(days=7)
        shifts = Shift.objects.filter(
            start_time__gte=monday,
            end_time__lte=sunday,
            shift_template__group__isnull=False,
        )
        if not shifts.exists():
            continue

        corrected_week = (
            shifts.first().shift_template.group.get_group_index() - delta
        ) % 4
        return ShiftTemplateGroup.get_group_from_index(corrected_week)

    return None


@register.simple_tag
def get_current_week_group() -> ShiftTemplateGroup:
    return get_week_group(timezone.now())
