from typing import Optional

from django.db import transaction
from django.db.models import Q

from tapir.shifts.models import (
    Shift,
    ShiftSlot,
    ShiftAttendance,
    StaffingStatusChoices,
    RecurringShiftWatch,
    ShiftWatch,
)


class ShiftWatchCreator:
    @classmethod
    def get_staffing_status_for_shift(
        cls, shift: Shift, last_status: str = None
    ) -> Optional[str]:
        """
        Compute the staffing status for a Shift instance by extracting the required
        counts and calling get_staffing_status_if_changed. Returns the status string or None.
        """
        valid_attendances_count = ShiftSlot.objects.filter(
            shift=shift,
            attendances__state=ShiftAttendance.State.PENDING,
        ).count()
        required_attendances_count = shift.get_num_required_attendances()
        number_of_available_slots = shift.slots.count()

        staffing_status = cls.get_staffing_status_if_changed(
            number_of_available_slots=number_of_available_slots,
            valid_attendances=valid_attendances_count,
            required_attendances=required_attendances_count,
            last_status=last_status,
        )

        return staffing_status

    @classmethod
    def get_initial_staffing_status_for_shift(
        cls, shift: Shift, last_status: str = None
    ) -> Optional[str]:
        """
        Compute the staffing status for a Shift instance by extracting the required
        counts and calling get_staffing_status_if_changed. Returns the status string or None.
        """
        staffing_status = cls.get_staffing_status_for_shift(shift=shift)

        if last_status is None and staffing_status is None:
            return StaffingStatusChoices.ALL_CLEAR

        return staffing_status

    @classmethod
    def calculate_staffing_status(
        cls,
        number_of_available_slots: int,
        valid_attendances: int,
        required_attendances: int,
        last_status: str = None,
    ):
        """Determine the staffing status based on attendance counts. Returns None if status has not changed."""
        if valid_attendances < required_attendances:
            return StaffingStatusChoices.UNDERSTAFFED
        # not understaffed - potentially states: : FULL, ALMOST_FULL, ALL_CLEAR
        remaining = number_of_available_slots - valid_attendances
        if remaining == 0:
            return StaffingStatusChoices.FULL
        if remaining == 1:
            return StaffingStatusChoices.ALMOST_FULL

        if last_status == StaffingStatusChoices.UNDERSTAFFED:
            return StaffingStatusChoices.ALL_CLEAR

        return None

    @classmethod
    def get_staffing_status_if_changed(
        cls,
        number_of_available_slots: int,
        valid_attendances: int,
        required_attendances: int,
        last_status: str = None,
    ) -> None | StaffingStatusChoices:

        current_status = cls.calculate_staffing_status(
            valid_attendances=valid_attendances,
            required_attendances=required_attendances,
            number_of_available_slots=number_of_available_slots,
            last_status=last_status,
        )
        if last_status != current_status:
            return current_status

        return None

    @classmethod
    def _filter_shifts_for_recurring(cls, recurring: RecurringShiftWatch):
        qs = Shift.objects.all()
        if recurring.weekdays or recurring.shift_template_group:
            if recurring.weekdays:
                iso = [d + 1 for d in recurring.weekdays]
                qs = qs.filter(start_time__iso_week_day__in=iso)
            if recurring.shift_template_group:
                qs = qs.filter(
                    shift_template__group__name__in=recurring.shift_template_group
                )
        elif recurring.shift_templates.exists():
            qs = qs.filter(shift_template__in=recurring.shift_templates.all())
        return qs

    @classmethod
    def create_shift_watches_for_recurring(cls, recurring: RecurringShiftWatch):
        shifts_qs = cls._filter_shifts_for_recurring(recurring)
        if not shifts_qs.exists():
            return

        existing_shift_ids = set(
            ShiftWatch.objects.filter(
                user=recurring.user, shift__in=shifts_qs
            ).values_list("shift_id", flat=True)
        )

        new_watches = []
        for shift in shifts_qs:
            if shift.pk in existing_shift_ids:
                continue
            new_watches.append(
                ShiftWatch(
                    user=recurring.user,
                    shift=shift,
                    staffing_status=list(recurring.staffing_status),
                    last_staffing_status=ShiftWatchCreator.get_initial_staffing_status_for_shift(
                        shift=shift, last_status=None
                    ),
                    recurring_template=recurring,
                )
            )

        if new_watches:
            ShiftWatch.objects.bulk_create(new_watches)

    @classmethod
    def create_shift_watch_entries(cls, shift: Shift) -> None:
        """For a shift, find relevant RecurringShiftWatches and create Shift-Watches."""
        shift_weekday = shift.start_time.weekday()
        filter_conditions = Q(weekdays__contains=[shift_weekday])
        if shift.shift_template:
            filter_conditions |= Q(shift_templates=shift.shift_template) | Q(
                shift_template_group__contains=[shift.shift_template.group.name]
            )
        relevant_recurrings = RecurringShiftWatch.objects.filter(filter_conditions)

        new_watches = []
        for template in relevant_recurrings:
            new_watches.append(
                ShiftWatch(
                    user=template.user,
                    shift=shift,
                    staffing_status=template.staffing_status,
                    recurring_template=template,
                    last_staffing_status=StaffingStatusChoices.ALL_CLEAR,
                )
            )

        if new_watches:
            ShiftWatch.objects.bulk_create(new_watches)
