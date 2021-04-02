from builtins import enumerate

from django import template

from tapir.accounts.models import TapirUser
from tapir.shifts.models import Shift, ShiftTemplate, ShiftAttendanceTemplate

register = template.Library()


@register.inclusion_tag("shifts/shift_block_tag.html", takes_context=True)
def shift_block(context, shift: Shift):
    context["shift"] = shift

    shift_attendance_states = ["empty" for _ in range(shift.num_slots)]
    shift_attendances = shift.get_valid_attendances()

    for index, attendance in enumerate(shift_attendances):
        shift_attendance_states[index] = "filled"
        if isinstance(context["user"], TapirUser) and attendance.user.id == context["user"].id:
            shift_attendance_states[0] = "user"
    context["shift_attendance_states"] = shift_attendance_states
    return context


@register.inclusion_tag("shifts/shift_template_block_tag.html", takes_context=True)
def shift_template_block(context, shift_template: ShiftTemplate):
    context["shift_template"] = shift_template

    attendance_states = ["empty" for _ in range(shift_template.num_slots)]
    attendances = ShiftAttendanceTemplate.objects.filter(shift_template=shift_template)
    for index, attendance in enumerate(attendances):
        attendance_states[index] = "filled"
        if isinstance(context["user"], TapirUser) and attendance.user.id == context["user"].id:
            attendance_states[0] = "user"

    context["attendance_states"] = attendance_states
    context["attendance_count"] = attendances.count()
    return context
