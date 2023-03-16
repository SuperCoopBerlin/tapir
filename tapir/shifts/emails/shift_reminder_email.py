from typing import List

from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts import config
from tapir.shifts.models import Shift


class ShiftReminderEmail(TapirEmailBase):
    shift = None

    def __init__(self, shift):
        self.shift = shift

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.shift_reminder"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift reminder")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent to a member %(days)s days before their shift") % {
            "days": config.REMINDER_EMAIL_DAYS_BEFORE_SHIFT
        }

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/shift_reminder.subject.html",
            "shifts/email/shift_reminder.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/shift_reminder.body.html",
            "shifts/email/shift_reminder.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {"shift": self.shift}

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
