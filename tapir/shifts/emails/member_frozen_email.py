from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.shifts.services.frozen_status_service import FrozenStatusService


class MemberFrozenEmail(TapirEmailBase):
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.member_frozen"

    @classmethod
    def get_name(cls) -> str:
        return _("Shift status set to frozen")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a member when their shift status gets set to frozen. Usually happens if they miss to many shifts."
        )

    def get_subject_templates(self) -> List:
        return [
            "shifts/email/member_frozen.subject.html",
            "shifts/email/member_frozen.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "shifts/email/member_frozen.body.html",
            "shifts/email/member_frozen.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
            "coop_name": settings.COOP_NAME,
            "threshold": FrozenStatusService.FREEZE_THRESHOLD,
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
