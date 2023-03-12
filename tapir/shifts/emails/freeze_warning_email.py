from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.config import FREEZE_THRESHOLD


class FreezeWarningEmail(TapirEmailBase):
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
            "shifts/email/freeze_warning.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/freeze_warning.body.html",
            "shifts/email/freeze_warning.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
            "coop_name": settings.COOP_NAME,
            "threshold": FREEZE_THRESHOLD,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        if not share_owner:
            return None
        mail = cls()
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
