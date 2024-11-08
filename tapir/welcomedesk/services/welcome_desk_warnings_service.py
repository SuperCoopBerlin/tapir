from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAttendanceMode
from tapir.welcomedesk.utils import get_display_name_for_welcome_desk


class WelcomeDeskWarningsService:
    @classmethod
    def optimize_queryset_for_this_service(
        cls, queryset: QuerySet[ShareOwner]
    ) -> QuerySet[ShareOwner]:
        return queryset.prefetch_related(
            "user",
            "user__shift_user_data",
            "user__shift_attendance_templates",
            "user__shift_user_data__shift_exemptions",
        )

    @classmethod
    def build_warnings(cls, share_owner: ShareOwner, request_user) -> list[str]:
        possible_warnings = {
            cls.should_show_abcd_shift_registration_warning: _(
                "%(name)s is not registered to an ABCD shift yet. Make sure they plan to do it!"
            ),
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
    def should_show_abcd_shift_registration_warning(share_owner: ShareOwner) -> bool:
        return (
            share_owner.user
            and share_owner.user.shift_user_data.attendance_mode
            == ShiftAttendanceMode.REGULAR
            and len(share_owner.user.shift_attendance_templates.all()) == 0
            and not share_owner.user.shift_user_data.is_currently_exempted_from_shifts()
        )

    @staticmethod
    def should_show_welcome_session_warning(share_owner: ShareOwner) -> bool:
        return not share_owner.attended_welcome_session
