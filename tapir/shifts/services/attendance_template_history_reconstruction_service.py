from django.utils import timezone
from icecream import ic

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftUserData,
    CreateShiftAttendanceTemplateLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
    UpdateShiftAttendanceStateLogEntry,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)


class AttendanceTemplateHistoryReconstructionService:
    @classmethod
    def reconstruct(cls, actor: TapirUser, dry_run=True):
        shift_user_datas = ShiftAttendanceModeService._annotate_queryset_with_has_abcd_attendance_at_datetime(
            ShiftUserData.objects.all(), timezone.now()
        )

        for shift_user_data in shift_user_datas.filter(
            **{ShiftAttendanceModeService.ANNOTATION_HAS_ABCD_ATTENDANCE_AT_DATE: True}
        ):
            tapir_user: TapirUser = shift_user_data.user
            if not tapir_user.shift_attendance_templates.exists():
                cls.reconstruct_user(tapir_user, actor, dry_run)

        for shift_user_data in shift_user_datas.filter(
            **{ShiftAttendanceModeService.ANNOTATION_HAS_ABCD_ATTENDANCE_AT_DATE: False}
        ):
            tapir_user: TapirUser = shift_user_data.user
            if tapir_user.shift_attendance_templates.exists():
                ic(tapir_user, "has attendance template but is annotated false")

    @classmethod
    def reconstruct_user(cls, tapir_user: TapirUser, actor: TapirUser, dry_run: bool):
        create_log_entries = CreateShiftAttendanceTemplateLogEntry.objects.filter(
            user=tapir_user
        )
        delete_log_entries = DeleteShiftAttendanceTemplateLogEntry.objects.filter(
            user=tapir_user
        )
        delete_log_entries = list(delete_log_entries)

        for create_log_entry in create_log_entries:
            corresponding_delete_log_entry_found = False
            for delete_log_entry in delete_log_entries:
                if delete_log_entry.shift_template == create_log_entry.shift_template:
                    delete_log_entries.remove(delete_log_entry)
                    corresponding_delete_log_entry_found = True
                    break
            if not corresponding_delete_log_entry_found:
                cls.reconstruct_from_create_log_entry(create_log_entry, actor, dry_run)
        if delete_log_entries:
            ic(tapir_user, "some delete log entries left", delete_log_entries)

    @classmethod
    def reconstruct_from_create_log_entry(
        cls,
        create_log_entry: CreateShiftAttendanceTemplateLogEntry,
        actor: TapirUser,
        dry_run: bool,
    ):
        last_log_entry = (
            UpdateShiftAttendanceStateLogEntry.objects.filter(
                user=create_log_entry.user,
                shift__shift_template=create_log_entry.shift_template,
            )
            .order_by("created_date")
            .last()
        )
        fake_time = create_log_entry.created_date
        if last_log_entry:
            fake_time = last_log_entry.created_date

        fake_attendance_template = ShiftAttendanceTemplate()
        fake_slot_template = False
        if (
            hasattr(create_log_entry, "slot_template")
            and create_log_entry.slot_template
        ):
            fake_attendance_template.slot_template = create_log_entry.slot_template
        else:
            fake_slot_template = True
            fake_attendance_template.slot_template = ShiftSlotTemplate()
            fake_attendance_template.slot_template.name = (
                CreateShiftAttendanceTemplateLogEntry.slot_template_name
            )
            fake_attendance_template.slot_template.shift_template = (
                create_log_entry.shift_template
            )
        delete_log_entry = DeleteShiftAttendanceTemplateLogEntry().populate(
            actor=actor,
            tapir_user=create_log_entry.user,
            shift_attendance_template=fake_attendance_template,
            comment="Reconstructed on 20.11.24",
        )
        if fake_slot_template:
            delete_log_entry.slot_template = None
        if dry_run:
            ic(
                "Would create",
                delete_log_entry,
                delete_log_entry.user,
                delete_log_entry.shift_template,
                fake_time,
            )
            return
        delete_log_entry.save()
        delete_log_entry.created_date = fake_time
        delete_log_entry.save()
