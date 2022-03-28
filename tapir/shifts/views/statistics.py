import datetime
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from django.views.generic import (
    TemplateView,
)

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    ShiftSlot,
    ShiftAttendanceMode,
    ShiftSlotTemplate,
    ShiftUserData,
    ShiftCycleEntry,
)
from tapir.utils.shortcuts import get_monday


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
        exempted_users = ShiftUserData.objects.filter(
            user__in=active_users
        ).is_covered_by_exemption()
        context["exempted_users_count"] = exempted_users.count()
        users_doing_shifts = active_users.exclude(shift_user_data__in=exempted_users)
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
            ] = TapirUser.objects.registered_to_shift_slot_name(
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
