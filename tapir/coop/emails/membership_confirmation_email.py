from typing import List

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop import pdfs
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase, all_emails


class MembershipConfirmationEmail(TapirEmailBase):
    share_owner = None

    def __init__(self, share_owner: ShareOwner):
        self.share_owner = share_owner

    @staticmethod
    def get_unique_id() -> str:
        return "tapir.coop.membership_confirmation.active"

    @staticmethod
    def get_name() -> str:
        return _("Membership confirmation for active users")

    @staticmethod
    def get_description() -> str:
        return _("")

    def get_subject_templates(self) -> List:
        status = "investing" if self.share_owner.is_investing else "active"
        return [
            f"coop/email/membership_confirmation.{status}.subject.html",
            f"coop/email/membership_confirmation.{status}.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        status = "investing" if self.share_owner.is_investing else "active"
        return [
            f"coop/email/membership_confirmation.{status}.body.html",
            f"coop/email/membership_confirmation.{status}.body.default.html",
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


all_emails[MembershipConfirmationEmail.get_unique_id()] = MembershipConfirmationEmail
