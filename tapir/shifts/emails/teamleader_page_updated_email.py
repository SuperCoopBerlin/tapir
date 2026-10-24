from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase


class TeamleaderPageUpdatedEmail(TapirEmailBuilderBase):
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.shifts.teamleader_page_updated"

    @classmethod
    def get_name(cls) -> str:
        return _("Teamleader page updated")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to all teamleaders when the content of the teamleader page gets updated by an employee."
        )

    def get_subject_templates(self) -> list:
        return [
            "shifts/email/teamleader_page_updated.subject.html",
        ]

    def get_body_templates(self) -> list:
        return [
            "shifts/email/teamleader_page_updated.body.html",
        ]

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
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
