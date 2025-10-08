import datetime
from django.shortcuts import render
from calendar import MONDAY
from collections import OrderedDict
from django.views.generic import TemplateView
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Q, F, Exists, OuterRef, Subquery
from tapir.shifts.models import (
    Shift,
    ShiftAttendance,
    WEEKDAY_CHOICES,
    ShiftTemplateGroup,
    ShiftTemplate,
    ShiftSlot,
)
from tapir.shifts.templatetags.shifts import shift_name_as_class
from tapir.shifts.utils import sort_slots_by_name
from tapir.shifts.utils import ColorHTMLCalendar, get_week_group
from tapir.utils.shortcuts import get_monday, set_header_for_file_download


# FIXME: should not be in views.py
def get_shift_slot_names():
    shift_slot_names = (
        ShiftSlot.objects.filter(shift__start_time__gt=timezone.now())
        .values_list("name", flat=True)
        .distinct()
    )
    shift_slot_names = [
        (shift_name_as_class(name), _(name)) for name in shift_slot_names if name != ""
    ]
    shift_slot_names.append(("", _("General")))
    return shift_slot_names


class UserDashboardView(LoginRequiredMixin,TemplateView):
    template_name = "shifts/user_dashboard.html"
    DATE_FORMAT = "%Y-%m-%d"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user


        date_from = timezone.now().date()
        date_to = date_from + datetime.timedelta(days=60)
        context["date_from"] = date_from.strftime(self.DATE_FORMAT)
        context["date_to"] = date_to.strftime(self.DATE_FORMAT)

        context["nb_days_for_self_unregister"] = Shift.NB_DAYS_FOR_SELF_UNREGISTER
        # Because the shift views show a lot of shifts,
        # we preload all related objects to avoid doing many database requests.
        # Filter for upcoming shifts the user can attend but isn't already attending
        
        # Create subquery to check if user has required capabilities for any slot in the shift
        user_capabilities = user.shift_user_data.capabilities.values_list('id', flat=True)
        
        # Subquery to find shifts where user can attend at least one slot
        attendable_slots_subquery = ShiftSlot.objects.filter(
            # Slot is available (no valid attendance or looking for stand-in)
            Q(attendances__isnull=True) | 
            Q(attendances__state=ShiftAttendance.State.LOOKING_FOR_STAND_IN),
            # User has required capabilities (if any required)
            Q(required_capabilities__isnull=True) | 
            Q(required_capabilities__in=user_capabilities),
            # User is active member
            shift__start_time__gt=timezone.now(),
            shift=OuterRef('pk'),
        ).exclude(
            # User not already attending this shift
            shift__slots__attendances__user=user,
            shift__slots__attendances__state__in=ShiftAttendance.VALID_STATES
        )
        
        # Get upcoming shifts with database-level filtering for availability and user eligibility
        shifts = (
            Shift.objects.prefetch_related("slots")
            .prefetch_related("slots__attendances")
            .prefetch_related("slots__attendances__user")
            .prefetch_related("slots__slot_template")
            .prefetch_related("slots__slot_template__attendance_template")
            .prefetch_related("slots__slot_template__attendance_template__user")
            .prefetch_related("shift_template")
            .prefetch_related("shift_template__group")
            .prefetch_related("slots__required_capabilities")
            .annotate(
                # Count total slots in the shift
                total_slots=Count("slots", distinct=True),
                # Count occupied slots (slots with valid attendances that are not looking for stand-in)
                occupied_slots=Count(
                    "slots__attendances",
                    filter=Q(
                        slots__attendances__state__in=[
                            ShiftAttendance.State.PENDING,
                            ShiftAttendance.State.DONE,
                        ]
                    ),
                    distinct=True
                ),
                # Check if user can attend any slot in this shift
                has_attendable_slots=Exists(attendable_slots_subquery)
            )
            .filter(
                start_time__gte=date_from,
                start_time__lt=date_to + datetime.timedelta(days=1),
                
                deleted=False,
                cancelled=False,
                # Shift has available slots (not completely full)
                occupied_slots__lt=F("total_slots"),
                # User can attend at least one slot
                has_attendable_slots=True,
            )
            .exclude(
                # Exclude shifts user is already attending with valid state
                slots__attendances__user=user,
                slots__attendances__state__in=ShiftAttendance.VALID_STATES
            )
            .order_by("start_time")[:200]
        )
        
        # Since we already filtered at database level, we just need to add attendable slots info
        # and deduplicate by slot type for display
        for shift in shifts:
            # Get unique slot types that user can attend
            attendable_slots = []
            seen_slot_types = set()
            
            # Use prefetched data to avoid additional queries
            for slot in shift.slots.all():
                # Quick check using prefetched data - most filtering already done at DB level
                if (not slot.get_valid_attendance() or 
                    slot.get_valid_attendance().state == ShiftAttendance.State.LOOKING_FOR_STAND_IN):
                    
                    # Use slot name as the type identifier, fallback to shift name if slot has no name
                    slot_type = slot.name if slot.name else shift.name
                    
                    # Only add if we haven't seen this slot type yet for this shift
                    if slot_type not in seen_slot_types:
                        attendable_slots.append(slot)
                        seen_slot_types.add(slot_type)
            
            # Add the attendable slots as an attribute for template use
            shift.attendable_slots = attendable_slots

        # Sort shifts by start time for the table display
        shifts = sorted(shifts, key=lambda s: s.start_time)
        
        # Separate urgent shifts (within 7 days and all slots empty) - use database annotation
        now = timezone.now()
        urgent_cutoff = now + datetime.timedelta(days=7)
        
        # Use list comprehension for better performance
        urgent_shifts = [
            shift for shift in shifts 
            if (shift.start_time <= urgent_cutoff and 
                shift.occupied_slots == 0)  # Use the database annotation
        ][:50]
        
        regular_shifts = [
            shift for shift in shifts 
            if not (shift.start_time <= urgent_cutoff and 
                   shift.occupied_slots == 0)
        ]
        
        # Calculate total available slots for each category
        total_available_slots = sum(len(shift.attendable_slots) for shift in regular_shifts)
        total_urgent_slots = sum(len(shift.attendable_slots) for shift in urgent_shifts)
        
        context["shifts"] = regular_shifts
        context["urgent_shifts"] = urgent_shifts
        context["total_available_slots"] = total_available_slots
        context["total_urgent_slots"] = total_urgent_slots
        context["shift_slot_names"] = get_shift_slot_names()
        
        return context