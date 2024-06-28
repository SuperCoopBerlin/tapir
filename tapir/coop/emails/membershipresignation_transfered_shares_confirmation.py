import os
from typing import List

from tapir import settings

from tapir.coop.models import ShareOwner, MembershipResignation
from tapir.core.tapir_email_base import TapirEmailBase
from django.utils.translation import gettext_lazy as _


class MembershipResignationTransferedSharesConfirmation(TapirEmailBase):
    def __init__(self, resigned_member: MembershipResignation):
        super().__init__()
        self.resigned_member = resigned_member

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.transfered_shares_confirmation"

    @classmethod
    def get_name(cls) -> str:
        return _("Confirmation Email for transfered shares.")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Automatically sent to the member who received shares after a resignation."
        )

    def get_subject_templates(self) -> List:
        return [
            "coop/email/membershipresignation_transfered_shares_confirmation_subject.html"
        ]

    def get_body_templates(self) -> List:
        return [
            "coop/email/membershipresignation_transfered_shares_confirmation_body.html"
        ]

    def get_extra_context(self) -> dict:
        return {
            "resigned_member": self.resigned_member.share_owner,
            "receiving_member": self.resigned_member.transfering_shares_to,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = ShareOwner.objects.filter(user__isnull=False).order_by("?")[0]
        mail = cls(resigned_member=share_owner)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
