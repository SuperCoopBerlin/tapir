from django.db.models import QuerySet, Exists, OuterRef

from tapir.shifts.models import ShiftAttendance, ShiftAttendanceTemplate


class IsShiftAttendanceFromTemplateService:
    ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE = "is_from_attendance_template"

    @classmethod
    def annotate_shift_attendances(cls, attendances: QuerySet[ShiftAttendance]):
        annotations = {
            cls.ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE: Exists(
                ShiftAttendanceTemplate.objects.filter(
                    user_id=OuterRef("user_id"),
                    slot_template_id=OuterRef("slot__slot_template_id"),
                )
            )
        }
        return attendances.annotate(**annotations)

    @classmethod
    def is_from_attendance_template(cls, attendance: ShiftAttendance):
        if not hasattr(attendance, cls.ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE):
            attendance = cls.annotate_shift_attendances(
                ShiftAttendance.objects.filter(id=attendance.id)
            ).first()
        return getattr(attendance, cls.ANNOTATION_IS_FROM_ATTENDANCE_TEMPLATE)
