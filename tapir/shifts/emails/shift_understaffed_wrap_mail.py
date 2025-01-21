from typing import List

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


from tapir.coop.models import ShareOwner
from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import Shift


class ShiftUnderstaffedWrapEmailBuilder(TapirEmailBuilderBase):
    option = MailOption.OPTIONAL_DISABLED

    def __init__(self, shifts: QuerySet[Shift]):
        super().__init__()
        self.shifts = shifts

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_understaffed_wrap_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift Understaffed (wrapped)")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when a shift is understaffed and user asked for wrap-ups."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed_wrap.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_understaffed_wrap.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {"shifts": self.shifts}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        shifts = Shift.objects.order_by("?")[:3]
        if not share_owner or not shifts:
            return None
        mail = cls(shifts=shifts)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
