from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db.models import Q, Value, Count
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    ShiftAttendanceTemplate,
    ShiftAttendance,
    DeleteShiftAttendanceTemplateLogEntry,
)
from tapir.utils.shortcuts import get_timezone_aware_datetime

if TYPE_CHECKING:
    from tapir.coop.models import ShareOwner, MembershipPause


class MembershipPauseService:
    ANNOTATION_HAS_ACTIVE_PAUSE = "has_active_pause"
    ANNOTATION_HAS_ACTIVE_PAUSE_AT_DATE = "has_active_pause_at_date"

    @staticmethod
    def on_pause_created_or_updated(pause: MembershipPause, actor: TapirUser | User):
        tapir_user: TapirUser = getattr(pause.share_owner, "user", None)
        if not tapir_user:
            return

        pause_start_as_datetime = get_timezone_aware_datetime(
            pause.start_date, datetime.time()
        )
        pause_end_as_datetime = (
            get_timezone_aware_datetime(
                pause.end_date, datetime.time(hour=23, minute=59)
            )
            if pause.end_date
            else None
        )

        for attendance_template in ShiftAttendanceTemplate.objects.filter(
            user=tapir_user
        ):
            attendance_template.cancel_attendances(pause_start_as_datetime)
            DeleteShiftAttendanceTemplateLogEntry().populate(
                actor=actor,
                tapir_user=tapir_user,
                shift_attendance_template=attendance_template,
                comment="Unregistered because of membership pause",
            ).save()
            attendance_template.delete()

        attendances = ShiftAttendance.objects.filter(
            user=tapir_user,
            slot__shift__start_time__gte=pause_start_as_datetime,
            state=ShiftAttendance.State.PENDING,
        )
        if pause_end_as_datetime:
            attendances = attendances.filter(
                slot__shift__end_time__lte=pause_end_as_datetime,
            )

        for attendance in attendances:
            attendance.state = ShiftAttendance.State.CANCELLED
            attendance.save()

    @classmethod
    def has_active_pause(cls, share_owner: ShareOwner, at_date: datetime.date = None):
        if at_date is None:
            at_date = timezone.now().date()

        if not hasattr(share_owner, cls.ANNOTATION_HAS_ACTIVE_PAUSE):
            return share_owner.membershippause_set.active_temporal(at_date).exists()

        annotated_active_date = getattr(
            share_owner, cls.ANNOTATION_HAS_ACTIVE_PAUSE_AT_DATE
        )
        if annotated_active_date != at_date:
            raise ValueError(
                f"Trying to check active pauses at date {at_date}, but the queryset has been "
                f"annotated relative to {annotated_active_date}"
            )
        return getattr(share_owner, cls.ANNOTATION_HAS_ACTIVE_PAUSE) > 0

    @classmethod
    def annotate_share_owner_queryset_with_has_active_pause(
        cls, queryset: ShareOwner.ShareOwnerQuerySet, at_date: datetime.date = None
    ):
        if at_date is None:
            at_date = timezone.now().date()

        filters = Q(membershippause__start_date__lte=at_date) & (
            Q(membershippause__end_date__gte=at_date)
            | Q(membershippause__end_date__isnull=True)
        )

        annotate_kwargs = {
            cls.ANNOTATION_HAS_ACTIVE_PAUSE: Count("membershippause", filter=filters),
            cls.ANNOTATION_HAS_ACTIVE_PAUSE_AT_DATE: Value(at_date),
        }
        return queryset.annotate(**annotate_kwargs)
