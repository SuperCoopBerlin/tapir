from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner
from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import Shift


class ShiftConfirmedEmailBuilder(TapirEmailBuilderBase):
    option = MailOption.OPTIONAL_DISABLED

    def __init__(self, shift):
        super().__init__()
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_confirmed"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift attendance confirmed")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent to a member when the member office marks the shift as confirmed")

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_confirmed.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_confirmed.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "shift": self.shift,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
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
