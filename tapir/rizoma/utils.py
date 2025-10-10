from tapir.shifts.models import ShiftSlot
from tapir.shifts.models import ShiftAttendance
from django.utils.translation import gettext_lazy as _
from tapir.shifts.templatetags.shifts import sort_slots_by_name
from tapir.shifts.templatetags.shifts import get_html_classes_for_filtering
from tapir.shifts.templatetags.shifts import template_group_name_to_character
from tapir.shifts.models import Shift

def get_attendance_details(slot: ShiftSlot) -> str:
    attendance = None
    for a in slot.attendances.all():
        if a.is_valid():
            attendance = a
            break

    if not attendance:
        return {
            "state": "empty",
            "slot": slot,
        }

    if attendance.state == ShiftAttendance.State.LOOKING_FOR_STAND_IN:
        return {
            "state": "standin",
            "slot": slot,
        }
    if (
        slot.slot_template is not None
        and hasattr(slot.slot_template, "attendance_template")
        and slot.slot_template.attendance_template.user == attendance.user
    ):
        return {
            "state": "regular",
            "user": slot.slot_template.attendance_template.user,
            "infos": slot.slot_template.attendance_template,
            "slot": slot,
        }

    return {
        "state": "single",
        "user": attendance.user,
        "slot": slot,
    }

def format_shift_for_template(shift: Shift, fill_parent: bool):
    attendances = {}

    slots = sort_slots_by_name(list(shift.slots.all()))

    for slot in slots:
        slot_name = slot.name
        if slot_name == "":
            slot_name = _("General")
        if slot_name not in attendances:
            attendances[slot_name] = []

        attendances[slot_name].append(get_attendance_details(slot))

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
    }

