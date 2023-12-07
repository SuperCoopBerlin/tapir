from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.models import Shift


class ShiftMissedEmail(TapirEmailBase):
    def __init__(self, shift):
        super().__init__()
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_missed"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift missed")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent to a member when the member office marks the shift as missed")

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_missed.subject.html",
            "shifts/email/shift_missed.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_missed.body.html",
            "shifts/email/shift_missed.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "shift": self.shift,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        shift = Shift.objects.order_by("?").first()
        if not shift or not share_owner:
            return None

        mail = cls(shift=shift)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
