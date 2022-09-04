from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop import pdfs
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase, all_emails


class MembershipConfirmationForInvestingMemberEmail(TapirEmailBase):
    share_owner = None

    def __init__(self, share_owner: ShareOwner):
        self.share_owner = share_owner

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.membership_confirmation.investing"

    @classmethod
    def get_name(cls) -> str:
        return _("Membership confirmation for investing users")

    @classmethod
    def get_description(cls) -> str:
        return ""

    def get_subject_templates(self) -> List:
        return [
            f"coop/email/membership_confirmation.investing.subject.html",
            f"coop/email/membership_confirmation.investing.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            f"coop/email/membership_confirmation.investing.body.html",
            f"coop/email/membership_confirmation.investing.body.default.html",
        ]

    def get_attachments(self) -> List:
        return [
            (
                "Mitgliedschaftsbestätigung %s.pdf"
                % self.share_owner.get_info().get_display_name(),
                pdfs.get_shareowner_membership_confirmation_pdf(
                    self.share_owner
                ).write_pdf(),
                "application/pdf",
            )
        ]

    def get_extra_context(self) -> dict:
        return {"organization_name": settings.COOP_NAME}

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = ShareOwner.objects.filter(user__isnull=True).order_by("?").first()
        if not share_owner:
            return None
        mail = cls(share_owner=share_owner)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail


all_emails[
    MembershipConfirmationForInvestingMemberEmail.get_unique_id()
] = MembershipConfirmationForInvestingMemberEmail
