from typing import List

from django.utils.translation import gettext_lazy as _


from tapir.coop.models import ShareOwner
from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import Shift


class ShiftUnderstaffedWatchEmailBuilder(TapirEmailBuilderBase):
    option = MailOption.OPTIONAL_DISABLED

    def __init__(self, shift):
        super().__init__()
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_understaffed_wrap_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Watched Shift Understaffed")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when a shift is understaffed and the user is watching this shift."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed_watch.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed_watch.body.html",
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
