from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.config import URL_MEMBER_MANUAL
from tapir.coop.models import ShareOwner
from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.config import (
    FREEZE_THRESHOLD,
    FREEZE_AFTER_DAYS,
    NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS,
)
from tapir.shifts.models import ShiftUserData, Shift


class ShiftUnderstaffedEmailBuilder(TapirEmailBuilderBase):
    option = MailOption.OPTIONAL_ENABLED

    def __init__(self, shift):
        super().__init__()
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_understaffed_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift Understaffed")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when a shift is understaffed and the user agreed to receive this kind of mail."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {"shift": self.shift}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        shift = Shift.objects.order_by("?").first()
        if not share_owner or not shift:
            return None
        mail = cls(shift=shift)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
