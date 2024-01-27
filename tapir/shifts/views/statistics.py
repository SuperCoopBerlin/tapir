import csv
import datetime
from datetime import timedelta

from chartjs.views import JSONView
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import (
    TemplateView,
)

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.coop.views import CONTENT_TYPE_CSV
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftSlot,
    ShiftAttendanceMode,
    ShiftSlotTemplate,
    ShiftUserData,
    ShiftCycleEntry,
    SHIFT_ATTENDANCE_STATES,
    ShiftTemplate,
    ShiftAttendanceTemplate,
    UpdateShiftAttendanceStateLogEntry,
    ShiftAttendanceTakenOverLogEntry,
    UpdateShiftUserDataLogEntry,
)
from tapir.shifts.utils import get_attendance_mode_display
from tapir.statistics.utils import build_line_chart_data, FORMAT_TICKS_PERCENTAGE
from tapir.statistics.views import CacheDatesFromFirstShareToTodayMixin
from tapir.utils.shortcuts import get_monday, get_models_with_attribute_value_at_date


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "shifts/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["members"] = self.get_members_context()
        context["abcd_slots"] = self.get_abcd_slots_context()
        context["weeks"] = self.get_weeks_context()
        context["cycles"] = self.get_cycles_context()

        return context

    @staticmethod
    def get_members_context():
        context = {}

        active_members = ShareOwner.objects.with_status(MemberStatus.ACTIVE)
        active_users = TapirUser.objects.filter(share_owner__in=active_members)
        context["active_users_count"] = active_users.count()

        context["frozen_users_count"] = active_users.with_shift_attendance_mode(
            ShiftAttendanceMode.FROZEN
        ).count()

        exempted_users = ShiftUserData.objects.filter(
            user__in=active_users
        ).is_covered_by_exemption()
        context["exempted_users_count"] = exempted_users.count()
        users_doing_shifts = active_users.exclude(
            shift_user_data__in=exempted_users
        ).exclude(shift_user_data__attendance_mode=ShiftAttendanceMode.FROZEN)
        context["users_doing_shifts_count"] = users_doing_shifts.count()

        context["abcd_slots_count"] = ShiftSlotTemplate.objects.count()
        context["extra_abcd_slots_count"] = (
            context["abcd_slots_count"] - context["users_doing_shifts_count"]
        )

        members_in_abcd_system = users_doing_shifts.with_shift_attendance_mode(
            ShiftAttendanceMode.REGULAR
        )
        context["members_in_abcd_system_count"] = members_in_abcd_system.count()

        context[
            "members_in_flying_system_count"
        ] = active_users.with_shift_attendance_mode(ShiftAttendanceMode.FLYING).count()

        context["members_in_abcd_system_without_shift_attendance_count"] = (
            members_in_abcd_system.annotate(
                num_template_attendances=Count("shift_attendance_templates")
            )
            .filter(num_template_attendances=0)
            .count()
        )

        return context

    @staticmethod
    def get_abcd_slots_context():
        slot_types = ShiftSlotTemplate.objects.values("name").distinct()
        abcd_slots = {}
        for slot_type in slot_types:
            displayed_name = slot_type["name"]
            if displayed_name == "":
                displayed_name = "General"
            abcd_slots[displayed_name] = {}
            abcd_slots[displayed_name][
                "registered"
            ] = TapirUser.objects.registered_to_abcd_shift_slot_name(
                slot_type["name"]
            ).count()
            abcd_slots[displayed_name]["slot_count"] = ShiftSlotTemplate.objects.filter(
                name=slot_type["name"]
            ).count()
        return abcd_slots

    @staticmethod
    def get_weeks_context():
        context = {}
        today = datetime.date.today()
        weeks = {"Last": -1, "Current": 0, "Next": 1}
        for week, delta in weeks.items():
            week_context = {}
            monday = get_monday(today) + timedelta(weeks=delta)
            week_start = datetime.datetime.combine(
                monday, datetime.time(hour=0, minute=0), timezone.now().tzinfo
            )
            week_end = monday + datetime.timedelta(days=7)
            shifts = Shift.objects.filter(
                start_time__gte=week_start,
                end_time__lte=week_end,
            )
            week_context["shifts_count"] = shifts.count()
            week_context["slots_count"] = ShiftSlot.objects.filter(
                shift__in=shifts
            ).count()
            week_context["occupied_count"] = (
                ShiftAttendance.objects.filter(slot__shift__in=shifts)
                .with_valid_state()
                .count()
            )
            week_context["standin_search_count"] = ShiftAttendance.objects.filter(
                slot__shift__in=shifts,
                state=ShiftAttendance.State.LOOKING_FOR_STAND_IN,
            ).count()

            context[week] = week_context

        return context

    @staticmethod
    def get_cycles_context():
        cycles = []

        for value in (
            ShiftCycleEntry.objects.values("cycle_start_date")
            .distinct()
            .order_by("-cycle_start_date")
        ):
            date = value["cycle_start_date"]
            entries = ShiftCycleEntry.objects.filter(cycle_start_date=date)
            cycle = {
                "date": date,
                "nb_members_total": entries.count(),
                "nb_members_doing_shifts": entries.filter(
                    shift_account_entry__isnull=False
                ).count(),
            }
            cycles.append(cycle)

        return cycles


class ShiftAttendanceStatistics:
    # Théo 15.07.23 I intend to extend this with more attendance stats
    @classmethod
    def get_all_shift_slot_data(cls):
        return (
            ShiftSlot.objects.all()
            .prefetch_related("shift")
            .prefetch_related("shift__shift_template")
            .prefetch_related(
                Prefetch(
                    "attendances",
                    queryset=ShiftAttendance.objects.order_by("-last_state_update"),
                )
            )
            .prefetch_related("slot_template__attendance_template__user")
            .prefetch_related("attendances__user__shift_user_data")
            .prefetch_related("attendances__user")
            .prefetch_related("attendances__user__share_owner")
            .prefetch_related("attendances__account_entry")
            .order_by("shift__start_time")
        )


@permission_required(PERMISSION_SHIFTS_MANAGE)
def slot_data_csv_view(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={
            "Content-Disposition": 'attachment; filename="shift_attendance_data.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "slot_id",
            "shift_id",
            "attendance_id",
            "member_id",
            "shift_date",
            "shift_start_time",
            "shift_end_time",
            "shift_was_attended",
            "required_qualifications",
            "is_from_an_abcd_shift",
            "is_from_an_abcd_attendance",
            "attendee_shift_status",
            "attendance_status",
            "excused_reason",
            "previous_statuses",
        ]
    )
    for slot in ShiftAttendanceStatistics.get_all_shift_slot_data():
        slot: ShiftSlot
        done_or_last_updated_attendance: ShiftAttendance | None = None

        slot_attendances_as_list = [a for a in slot.attendances.all()]
        if slot_attendances_as_list:
            done_attendances = [
                a
                for a in slot_attendances_as_list
                if a.state == ShiftAttendance.State.DONE
            ]
            done_or_last_updated_attendance = (
                done_attendances[0] if done_attendances else None
            )
            if done_or_last_updated_attendance is None:
                # this gives the last updated attendance because they have already been sorted in the prefetch
                done_or_last_updated_attendance = slot_attendances_as_list[0]

        is_from_an_abcd_attendance = False
        if done_or_last_updated_attendance is not None:
            is_from_an_abcd_attendance = (
                hasattr(slot, "slot_template")
                and hasattr(slot.slot_template, "attendance_template")
                and slot.slot_template.attendance_template.user
                == done_or_last_updated_attendance.user
            )
        writer.writerow(
            [
                slot.id,  # slot_id
                slot.shift.id,  # shift_id
                done_or_last_updated_attendance.id
                if done_or_last_updated_attendance
                else "None",  # attendance_id,
                done_or_last_updated_attendance.user.get_member_number()
                if done_or_last_updated_attendance
                else "None",
                slot.shift.start_time.date(),  # shift_date
                timezone.localtime(slot.shift.start_time).strftime(
                    "%H:%M"
                ),  # shift_start_time
                timezone.localtime(slot.shift.end_time).strftime(
                    "%H:%M"
                ),  # shift_end_time
                len(
                    [
                        attendance
                        for attendance in slot.attendances.all()
                        if attendance.state == ShiftAttendance.State.DONE
                    ]
                )
                > 0,  # shift_was_attended
                ",".join(slot.required_capabilities),  # required_qualifications
                slot.shift.shift_template is not None,  # is_from_an_abcd_shift
                is_from_an_abcd_attendance,  # is_from_an_abcd_attendance
                get_attendance_mode_display(
                    done_or_last_updated_attendance.user.shift_user_data.attendance_mode
                )
                if done_or_last_updated_attendance
                else "None",  # attendee_shift_status
                SHIFT_ATTENDANCE_STATES[done_or_last_updated_attendance.state]
                if done_or_last_updated_attendance
                else "None",  # attendance_status
                done_or_last_updated_attendance.account_entry.description.replace(
                    done_or_last_updated_attendance.slot.get_display_name(), ""
                )
                if done_or_last_updated_attendance
                and done_or_last_updated_attendance.account_entry
                else "None",
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def shift_template_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={"Content-Disposition": 'attachment; filename="abcd_shift_data.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "abcd_shift_id",
            "group_name",
            "name",
            "start_time",
            "end_time",
            "weekday (monday=0)",
        ]
    )
    for shift_template in (
        ShiftTemplate.objects.all().prefetch_related("group").order_by("id")
    ):
        shift_template: ShiftTemplate
        writer.writerow(
            [
                shift_template.id,
                shift_template.group.name,
                shift_template.name,
                shift_template.start_time,
                shift_template.end_time,
                shift_template.weekday,
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def shift_slot_template_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={
            "Content-Disposition": 'attachment; filename="abcd_shift_slot_data.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "abcd_shift_slot_id",
            "name",
            "abcd_shift_id",
            "required_capabilities",
        ]
    )
    for shift_slot_template in (
        ShiftSlotTemplate.objects.all()
        .prefetch_related("shift_template")
        .order_by("id")
    ):
        shift_slot_template: ShiftSlotTemplate
        writer.writerow(
            [
                shift_slot_template.id,
                shift_slot_template.name,
                shift_slot_template.shift_template.id,
                shift_slot_template.get_required_capabilities_display(),
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def shift_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={"Content-Disposition": 'attachment; filename="shift_data.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "shift_id",
            "date",
            "start_time",
            "end_time",
            "name",
            "cancelled_reason",
            "template_id",
        ]
    )
    for shift in Shift.objects.all().prefetch_related("shift_template").order_by("id"):
        writer.writerow(
            [
                shift.id,
                shift.start_time.date(),
                timezone.localtime(shift.start_time).strftime("%H:%M"),
                timezone.localtime(shift.end_time).strftime("%H:%M"),
                shift.name,
                shift.cancelled_reason if shift.cancelled else "Not cancelled",
                shift.shift_template.id
                if hasattr(shift, "shift_template") and shift.shift_template
                else "None",
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def shift_slot_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={"Content-Disposition": 'attachment; filename="shift_slot_data.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(
        ["shift_slot_id", "name", "shift_id", "abcd_slot_id", "required_capabilities"]
    )
    for shift_slot in (
        ShiftSlot.objects.all()
        .prefetch_related("slot_template")
        .prefetch_related("shift")
        .order_by("id")
    ):
        shift_slot: ShiftSlot
        writer.writerow(
            [
                shift_slot.id,
                shift_slot.name,
                shift_slot.shift.id,
                shift_slot.slot_template.id
                if hasattr(shift_slot, "slot_template") and shift_slot.slot_template
                else "None",
                shift_slot.get_required_capabilities_display(),
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def attendance_template_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={
            "Content-Disposition": 'attachment; filename="abcd_attendance_data.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(["abcd_attendance_id", "member_id", "abcd_slot_id"])
    for attendance_template in (
        ShiftAttendanceTemplate.objects.all()
        .prefetch_related("user")
        .prefetch_related("user__share_owner")
        .prefetch_related("slot_template")
        .order_by("id")
    ):
        attendance_template: ShiftAttendanceTemplate
        writer.writerow(
            [
                attendance_template.id,
                attendance_template.user.get_member_number(),
                attendance_template.slot_template.id,
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def attendance_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={"Content-Disposition": 'attachment; filename="attendance_data.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "attendance_id",
            "slot_id",
            "shift_id",
            "member_id",
            "user_postcode",
            "attendance_template_id",
            "state",
            "excused_reason",
            "member_shift_mode_at_time_of_shift",
        ]
    )
    for attendance in (
        ShiftAttendance.objects.all()
        .prefetch_related("slot")
        .prefetch_related("slot__shift")
        .prefetch_related("user")
        .prefetch_related("user__share_owner")
        .prefetch_related("slot__slot_template__attendance_template__user")
        .order_by("id")
    ):
        attendance: ShiftAttendance
        attendance_template_id = "None"
        is_from_an_abcd_attendance = (
            hasattr(attendance.slot, "slot_template")
            and hasattr(attendance.slot.slot_template, "attendance_template")
            and attendance.slot.slot_template.attendance_template.user
            == attendance.user
        )
        if is_from_an_abcd_attendance:
            attendance_template_id = (
                attendance.slot.slot_template.attendance_template.id
            )
        writer.writerow(
            [
                attendance.id,
                attendance.slot.id,
                attendance.slot.shift.id,
                attendance.user.get_member_number(),
                attendance.user.postcode,
                attendance_template_id,
                SHIFT_ATTENDANCE_STATES[attendance.state],
                attendance.excused_reason if attendance.excused_reason else "None",
                "TODO",
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def attendance_update_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={
            "Content-Disposition": 'attachment; filename="attendance_updates_data.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "shift_attendance_update_id",
            "date",
            "state",
            "shift_id",
            "update",
        ]
    )
    for log_entry in (
        UpdateShiftAttendanceStateLogEntry.objects.all()
        .prefetch_related("shift")
        .order_by("id")
    ):
        log_entry: UpdateShiftAttendanceStateLogEntry
        writer.writerow(
            [
                log_entry.id,
                log_entry.created_date,
                log_entry.state,
                log_entry.shift.id,
                log_entry.values,
            ],
        )

    return response


@permission_required(PERMISSION_SHIFTS_MANAGE)
def attendance_takeover_data_csv_export(_):
    response = HttpResponse(
        content_type=CONTENT_TYPE_CSV,
        headers={
            "Content-Disposition": 'attachment; filename="attendance_takeover_data.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "shift_attendance_takeover_id",
            "date",
            "state",
            "shift_id",
            "update",
        ]
    )
    for log_entry in (
        ShiftAttendanceTakenOverLogEntry.objects.all()
        .prefetch_related("shift")
        .order_by("id")
    ):
        log_entry: ShiftAttendanceTakenOverLogEntry
        writer.writerow(
            [
                log_entry.id,
                log_entry.created_date,
                log_entry.state,
                log_entry.shift.id,
                log_entry.values,
            ],
        )

    return response


class ShiftStatusEvolutionJsonView(CacheDatesFromFirstShareToTodayMixin, JSONView):
    def get_context_data(self, **kwargs):
        return build_line_chart_data(
            x_axis_values=[date.strftime("%Y-%m") for date in self.get_dates()],
            y_axis_values=self.get_data(),
            data_labels=[
                choice[1] for choice in ShiftUserData.SHIFT_ATTENDANCE_MODE_CHOICES
            ],
            y_axis_min=0,
            y_axis_max=1,
            stacked=True,
            format_ticks=FORMAT_TICKS_PERCENTAGE,
        )

    def get_data(self):
        result = {}
        for mode in ShiftUserData.SHIFT_ATTENDANCE_MODE_CHOICES:
            result[mode[0]] = []

        for date in self.get_dates():
            result_at_date = {}
            for mode in ShiftUserData.SHIFT_ATTENDANCE_MODE_CHOICES:
                result_at_date[
                    mode[0]
                ] = self.get_number_of_members_with_attendance_mode_at_date(
                    mode[0], date
                )
            total = sum(result_at_date.values())

            for mode in ShiftUserData.SHIFT_ATTENDANCE_MODE_CHOICES:
                result[mode[0]].append(
                    (result_at_date[mode[0]] / total) if total else 0
                )

        return result.values()

    def get_dates(self):
        return self.get_and_cache_dates_from_first_share_to_today(
            min_date=datetime.date(year=2022, month=1, day=1)
        )

    @staticmethod
    def get_number_of_members_with_attendance_mode_at_date(
        mode: str, date: datetime.datetime
    ):
        entries = (
            ShiftUserData.objects.all()
            .filter(
                user__share_owner__in=ShareOwner.objects.with_status(
                    MemberStatus.ACTIVE, date
                )
            )
            .select_related("user")
        )
        return len(
            get_models_with_attribute_value_at_date(
                entries,
                UpdateShiftUserDataLogEntry,
                "attendance_mode",
                mode,
                date,
                lambda shift_user_data: shift_user_data.user,
            )
        )
