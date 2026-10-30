from django.utils.translation import gettext_lazy as _

from tapir.coop.config import URL_MEMBER_MANUAL
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.shifts.models import UserCapability


class CapabilityExpiresEmailBuilder(TapirEmailBuilderBase):
    def __init__(self, usercapability: UserCapability):
        super().__init__()
        self.usercapability = usercapability

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.capability_expires"

    @classmethod
    def get_name(cls) -> str:
        return _("Qualification expires")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent to a member when their qualificiation is about to expire.")

    def get_subject_templates(self) -> list:
        return [
            "shifts/email/capability_expires.subject.html",
        ]

    def get_body_templates(self) -> list:
        return [
            "shifts/email/capability_expires.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "capability": self.usercapability.capability,
            "end_date": self.usercapability.get_effective_end_date(),
            "url_member_manual": URL_MEMBER_MANUAL,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        capability = UserCapability.objects.first()
        if not capability:
            return None
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        if not share_owner:
            return None
        mail = cls(usercapability=capability)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
