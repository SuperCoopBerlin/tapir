from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.models import Shift


class StandInFoundEmail(TapirEmailBase):
    shift = None

    def __init__(self, shift):
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.stand_in_found"

    @classmethod
    def get_name(cls) -> str:
        return _("Stand-in found")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member that was looking for a stand-in "
            "when the corresponding slot is taken over by another member."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/stand_in_found.subject.html",
            "shifts/email/stand_in_found.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/stand_in_found.body.html",
            "shifts/email/stand_in_found.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "shift": self.shift,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
            "coop_name": settings.COOP_NAME,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
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
