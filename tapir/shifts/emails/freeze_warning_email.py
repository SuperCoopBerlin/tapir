from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.config import URL_MEMBER_MANUAL
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.config import (
    FREEZE_THRESHOLD,
    FREEZE_AFTER_DAYS,
    NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
)
from tapir.shifts.models import ShiftUserData


class FreezeWarningEmail(TapirEmailBase):
    def __init__(self, shift_user_data: ShiftUserData):
        super().__init__()
        self.shift_user_data = shift_user_data

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.freeze_warning"

    @classmethod
    def get_name(cls) -> str:
        return _("Freeze warning")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when their shift status is not frozen yet but will "
            "be set to frozen if they don't register for make-up shifts."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/freeze_warning.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/freeze_warning.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
            "coop_name": settings.COOP_NAME,
            "threshold": FREEZE_THRESHOLD,
            "freeze_after_days": FREEZE_AFTER_DAYS,
            "nb_weeks_in_the_future": NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
            "account_balance": self.shift_user_data.get_account_balance(),
            "url_member_manual": URL_MEMBER_MANUAL,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        if not share_owner:
            return None
        mail = cls(share_owner.user.shift_user_data)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
