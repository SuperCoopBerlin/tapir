from typing import List

from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.models import Shift


class ShiftUnderstaffedEmail(TapirEmailBase):
    default = False
    mandatory = False

    def __init__(self, shifts: List[Shift]):
        super().__init__()
        self.shifts = shifts

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_warning"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift is understaffed warning")

    @classmethod
    def get_description(cls) -> str:
        return _(
            f"Sent to all members, if a shift is understaffed. Time span is defined shift-wise"
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed.subject.html",
            "shifts/email/shift_understaffed.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed.body.html",
            "shifts/email/shift_understaffed.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {"shifts": self.shifts}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        shifts = Shift.objects.order_by("?")[:10]
        if not share_owner or not shifts:
            return None
        mail = cls(shifts=shifts)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
