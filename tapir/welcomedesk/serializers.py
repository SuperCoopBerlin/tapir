import datetime

from django.core.handlers.wsgi import WSGIRequest
from rest_framework import serializers

from tapir.coop.models import ShareOwner
from tapir.coop.services.InvestingStatusService import InvestingStatusService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.shifts.models import ShiftAttendanceMode, ShiftAttendanceTemplate
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.utils.user_utils import UserUtils
from django.utils.translation import gettext_lazy as _


class ShareOwnerForWelcomeDeskSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    can_shop = serializers.SerializerMethodField()
    co_purchaser = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField()
    reasons_cannot_shop = serializers.SerializerMethodField()

    class Meta:
        model = ShareOwner
        fields = [
            "id",
            "display_name",
            "can_shop",
            "co_purchaser",
            "warnings",
            "reasons_cannot_shop",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request: WSGIRequest = self.context.get("request")
        self.reference_time: datetime.datetime = self.context.get("reference_time")
        self.reference_date: datetime.date = self.context.get("reference_date")

    def get_display_name(self, share_owner: ShareOwner) -> str:
        display_type = UserUtils.should_viewer_see_short_or_long_display_type(
            self.request.user
        )
        if display_type == UserUtils.DISPLAY_NAME_TYPE_SHORT:
            display_type = UserUtils.DISPLAY_NAME_TYPE_WELCOME_DESK
        return UserUtils.build_display_name(share_owner, display_type)

    def get_can_shop(self, share_owner: ShareOwner) -> bool:
        return share_owner.can_shop(self.reference_time)

    @staticmethod
    def get_co_purchaser(share_owner: ShareOwner) -> str | None:
        if not share_owner.user:
            return None
        return share_owner.user.co_purchaser

    def get_warnings(self, share_owner: ShareOwner) -> list[str]:
        warnings = []

        if (
            share_owner.user
            and share_owner.user.shift_user_data.attendance_mode
            == ShiftAttendanceMode.REGULAR
            and not ShiftAttendanceTemplate.objects.filter(
                user=share_owner.user
            ).exists()
            and not share_owner.user.shift_user_data.is_currently_exempted_from_shifts()
        ):
            warnings.append(
                _(
                    "%(name)s is not registered to an ABCD shift yet. Make sure they plan to do it!"
                    % {"name": self.get_display_name(share_owner)}
                )
            )

        if not share_owner.attended_welcome_session:
            warnings.append(
                _(
                    "%(name)s has not attended a welcome session yet. Make sure they plan to do it!"
                    % {"name": self.get_display_name(share_owner)}
                )
            )

        return warnings

    def get_reasons_cannot_shop(self, share_owner: ShareOwner) -> list[str]:
        reasons = []

        if not share_owner.user:
            reasons.append(
                _(
                    "%(name)s does not have a Tapir account. Contact a member of the management team."
                )
            )

        if InvestingStatusService.is_investing(share_owner, self.reference_time):
            reasons.append(
                _(
                    "%(name)s is an investing member. If they want to shop, they have to become an active member. "
                    "Contact a member of the management team."
                )
            )

        if (
            share_owner.user
            and ShiftAttendanceModeService.get_attendance_mode(
                share_owner.user.shift_user_data, self.reference_date
            )
            == ShiftAttendanceMode.FROZEN
        ):
            reasons.append(
                _(
                    "%(name)s has been frozen because they missed too many shifts."
                    "If they want to shop, they must first be re-activated."
                    "Contact a member of the management team."
                )
            )

        if MembershipPauseService.has_active_pause(share_owner, self.reference_date):
            reasons.append(
                _(
                    "%(name)s has paused their membership. Contact a member of the management team."
                )
            )

        reasons = [
            reason % {"name": self.get_display_name(share_owner)} for reason in reasons
        ]

        return reasons
