import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.welcomedesk.utils import get_display_name_for_welcome_desk


class WelcomeDeskWarningsService:
    @classmethod
    def optimize_queryset_for_this_service(
        cls, queryset: QuerySet[ShareOwner], reference_time: datetime.datetime
    ) -> QuerySet[ShareOwner]:
        queryset = queryset.prefetch_related(
            "user",
            "user__shift_user_data",
            "user__shift_attendance_templates",
            "user__shift_user_data__shift_exemptions",
        )
        queryset = ShiftAttendanceModeService.annotate_share_owner_queryset_with_attendance_mode_at_datetime(
            queryset, reference_time
        )

        return queryset

    @classmethod
    def build_warnings(cls, share_owner: ShareOwner, request_user) -> list[str]:
        possible_warnings = {
            cls.should_show_welcome_session_warning: _(
                "%(name)s has not attended a welcome session yet. Make sure they plan to do it!"
            ),
        }

        return [
            message
            % {"name": get_display_name_for_welcome_desk(share_owner, request_user)}
            for check, message in possible_warnings.items()
            if check(share_owner=share_owner)
        ]

    @staticmethod
    def should_show_welcome_session_warning(share_owner: ShareOwner) -> bool:
        return not share_owner.attended_welcome_session
