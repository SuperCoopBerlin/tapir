from typing import List

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tapir.coop.services.MemberInfoService import MemberInfoService

from tapir import settings
from tapir.coop import pdfs
from tapir.coop.models import ShareOwner
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.tapir_email_base import TapirEmailBase
from tapir.utils.user_utils import UserUtils


class MembershipConfirmationForInvestingMemberEmail(TapirEmailBase):
    def __init__(self, share_owner: ShareOwner):
        super().__init__()
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
            "coop/email/membership_confirmation.investing.subject.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "coop/email/membership_confirmation.investing.body.html",
        ]

    def get_attachments(self) -> List:
        return [
            (
                "Mitgliedschaftsbestätigung %s.pdf"
                % UserUtils.build_display_name(
                    self.share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL
                ),
                pdfs.get_shareowner_membership_confirmation_pdf(
                    self.share_owner,
                    num_shares=MemberInfoService.get_number_of_active_shares(
                        self.share_owner
                    ),
                    date=timezone.now().date(),
                ).write_pdf(),
                CONTENT_TYPE_PDF,
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
