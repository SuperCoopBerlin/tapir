from typing import List

from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import MembershipResignation
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase


class MembershipResignationTransferredSharesConfirmation(TapirEmailBuilderBase):
    def __init__(self, member_resignation: MembershipResignation):
        super().__init__()
        self.member_resignation = member_resignation

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.transferred_shares_confirmation"

    @classmethod
    def get_name(cls) -> str:
        return _("Confirmation Email for transferred shares.")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Automatically sent to the member who received shares after a resignation."
        )

    def get_subject_templates(self) -> List:
        return [
            "coop/email/membershipresignation_transferred_shares_confirmation_subject.html"
        ]

    def get_body_templates(self) -> List:
        return [
            "coop/email/membershipresignation_transferred_shares_confirmation_body.html"
        ]

    def get_extra_context(self) -> dict:
        return {
            "resigned_member": self.member_resignation.share_owner,
            "receiving_member": self.member_resignation.transferring_shares_to,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        member_resignation = (
            MembershipResignation.objects.filter(transferring_shares_to__isnull=False)
            .order_by("?")
            .first()
        )

        if not member_resignation:
            return None

        mail = cls(member_resignation=member_resignation)
        mail.get_full_context(
            share_owner=member_resignation.share_owner,
            member_infos=member_resignation.share_owner.get_info(),
            tapir_user=member_resignation.share_owner.user,
        )
        return mail
