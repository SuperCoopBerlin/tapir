import datetime

from django import template
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import tapir.shifts.config
from tapir.shifts import utils
from tapir.shifts.models import (
    Shift,
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftAttendance,
    ShiftTemplateGroup,
    ShiftSlot,
    ShiftUserData,
    ShiftWatch,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.utils.shortcuts import get_monday, ensure_date

register = template.Library()


@register.inclusion_tag("shifts/user_shifts_overview_tag.html", takes_context=True)
def user_shifts_overview(context, user):
    context["user"] = user
    now = timezone.now()
    context["next_watched_shift"] = (
        ShiftWatch.objects.filter(user=user, shift__end_time__gte=now)
        .select_related("shift")
        .order_by("shift__end_time")
        .first()
    )
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

    # order by length of name so that the shift name does not interfere with header
    # we can't use shift.slots.all().order_by(Length("name").asc()),
    # because we that would load the slots again from the database.
    # Instead, we want to use the preloaded slots coming from prefetch_related() in the view
    slots = [slot for slot in shift.slots.all()]
    slots.sort(key=lambda slot: len(slot.name))

    for slot in slots:
        slot_name = slot.name
        if slot_name == "":
            slot_name = _("General")
        if slot_name not in attendances:
            attendances[slot_name] = []

        attendances[slot_name].append(get_attendance_state_for_html_icon(slot))

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
        "filter_classes": " ".join(get_html_classes_for_filtering(shift)),
        "flexible_time": shift.flexible_time,
        "is_watching": getattr(shift, "is_watching", False),
    }


def get_attendance_state_for_html_icon(slot: ShiftSlot) -> str:
    attendance = None
    for a in slot.attendances.all():
        if a.is_valid():
            attendance = a
            break

    if not attendance:
        return "empty"

    if attendance.state == ShiftAttendance.State.LOOKING_FOR_STAND_IN:
        return "standin"
    if (
        slot.slot_template is not None
        and hasattr(slot.slot_template, "attendance_template")
        and slot.slot_template.attendance_template.user == attendance.user
    ):
        return "regular"
    return "single"


def get_html_classes_for_filtering(shift: Shift) -> set:
    if shift.cancelled:
        return {"cancelled"}

    if not shift.is_in_the_future():
        return {"is_in_the_past"}

    filter_classes = set()
    num_valid_attendances = 0
    for slot in shift.slots.all():
        valid_attendance = None
        for a in slot.attendances.all():
            if a.is_valid():
                valid_attendance = a
                break

        if valid_attendance and valid_attendance.state == ShiftAttendance.State.PENDING:
            num_valid_attendances += 1

        if (
            not valid_attendance
            or valid_attendance.state == ShiftAttendance.State.LOOKING_FOR_STAND_IN
        ):
            filter_classes.add("freeslot_any")
            filter_classes.add("freeslot_" + shift_name_as_class(slot.name))

    if num_valid_attendances < shift.get_num_required_attendances():
        filter_classes.add("needs_help")

    return filter_classes


def shift_template_to_block_object(shift_template: ShiftTemplate, fill_parent: bool):
    attendances = {}

    filter_classes = set()

    num_attendances = 0

    # order by length of name so that the shift name does not interfere with header
    # we can't use shift_template.slot_templates.all().order_by(...)
    # because we that would load the slots again from the database.
    # Instead, we want to use the preloaded slots coming from prefetch_related() in the view
    slot_templates = [
        slot_template for slot_template in shift_template.slot_templates.all()
    ]
    slot_templates.sort(key=lambda slot_template: len(slot_template.name))

    for slot_template in slot_templates:
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
        "filter_classes": " ".join(filter_classes),
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
def get_week_group(
    target_date, cycle_start_dates=None, shift_groups_count: int | None = None
) -> ShiftTemplateGroup | None:
    if shift_groups_count is None:
        shift_groups_count = ShiftTemplateGroup.objects.count()

    if shift_groups_count == 0:
        # Many tests run without creating any ShiftTemplateGroup but still call get_week_group
        return None

    target_date = ensure_date(target_date)
    target_date = get_monday(target_date)

    if cycle_start_dates is None:
        cycle_start_dates = tapir.shifts.config.cycle_start_dates

    if cycle_start_dates[0] > target_date:
        ref_date = cycle_start_dates[0]
    else:
        # Get the highest date that is before target_date
        ref_date = [
            get_monday(cycle_start_date)
            for cycle_start_date in cycle_start_dates
            if cycle_start_date <= target_date
        ][-1]
    delta_weeks = ((target_date - ref_date).days / 7) % shift_groups_count
    return ShiftTemplateGroup.get_group_from_index(delta_weeks)


@register.simple_tag
def get_current_week_group() -> ShiftTemplateGroup:
    return get_week_group(timezone.now())


@register.simple_tag
def get_used_solidarity_shifts_current_year(shift_user_data):
    return ShiftUserData.get_used_solidarity_shifts_current_year(shift_user_data)


@register.simple_tag
def get_attendance_mode_display(shift_user_data: ShiftUserData) -> str:
    return utils.get_attendance_mode_display(
        ShiftAttendanceModeService.get_attendance_mode(shift_user_data)
    )


@register.filter(name="user_watching_shift")
def user_watching_shift(user, shift) -> QuerySet:
    return ShiftWatch.objects.filter(user=user, shift=shift)


@register.filter(name="weekday_labels")
def weekday_labels(value):
    _mapping = dict(WEEKDAY_CHOICES)
    if not value:
        return []
    return [_mapping.get(i, str(i)) for i in value]


@register.simple_tag
def shiftwatch_display_without_user(shiftwatch: ShiftWatch):
    recurring_part = ""
    staffing_status = ""
    if shiftwatch.recurring_template:
        recurring_part = format_html(
            ' based on <span class="text-muted">#{}</span>',
            shiftwatch.recurring_template.id,
        )
    else:
        staffing_status = "for changes of " + ", ".join(
            status for status in shiftwatch.staffing_status
        )
    return format_html(
        '<a href="{}">{}</a> {}{}',
        shiftwatch.shift.get_absolute_url(),
        shiftwatch.shift.get_display_name(),
        staffing_status,
        recurring_part,
    )
