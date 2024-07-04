from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.coop.config import feature_flag_membership_resignation
from tapir.core.config import sidebar_link_groups
from tapir.settings import (
    PERMISSION_COOP_MANAGE,
    PERMISSION_ACCOUNTING_VIEW,
    PERMISSION_COOP_VIEW,
)


class CoopConfig(AppConfig):
    name = "tapir.coop"

    def ready(self):
        self.register_sidebar_link_groups()
        self.register_emails()

        from tapir.core.models import FeatureFlag

        FeatureFlag.ensure_flag_exists(feature_flag_membership_resignation)

    @staticmethod
    def register_sidebar_link_groups():
        members_group = sidebar_link_groups.get_group(_("Members"), 1)

        members_group.add_link(
            display_name=_("Applicants"),
            material_icon="person_outline",
            url=reverse_lazy("coop:draftuser_list"),
            ordering=1,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        members_group.add_link(
            display_name=_("Members"),
            material_icon="person",
            url=reverse_lazy("coop:shareowner_list"),
            ordering=2,
            required_permissions=[PERMISSION_COOP_VIEW],
        )

        members_group.add_link(
            display_name=_("Member management"),
            material_icon="settings",
            url=reverse_lazy("coop:management"),
            ordering=3,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        management_group = sidebar_link_groups.get_group(_("Management"), 2)

        management_group.add_link(
            display_name=_("Incoming payments"),
            material_icon="euro",
            url=reverse_lazy("coop:incoming_payment_list"),
            ordering=3,
            required_permissions=[PERMISSION_ACCOUNTING_VIEW],
        )

    @staticmethod
    def register_emails():
        from tapir.core.tapir_email_base import TapirEmailBase
        from tapir.coop.emails.extra_shares_confirmation_email import (
            ExtraSharesConfirmationEmail,
        )
        from tapir.coop.emails.membership_confirmation_email_for_active_member import (
            MembershipConfirmationForActiveMemberEmail,
        )
        from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
            MembershipConfirmationForInvestingMemberEmail,
        )
        from tapir.coop.emails.tapir_account_created_email import (
            TapirAccountCreatedEmail,
        )
        from tapir.coop.emails.co_purchaser_updated_mail import (
            CoPurchaserUpdatedMail,
        )
        from tapir.coop.emails.membershipresignation_confirmation_email import (
            MembershipResignationConfirmation,
        )
        from tapir.coop.emails.membershipresignation_transfered_shares_confirmation import (
            MembershipResignationTransferedSharesConfirmation,
        )

        TapirEmailBase.register_email(ExtraSharesConfirmationEmail)
        TapirEmailBase.register_email(MembershipConfirmationForActiveMemberEmail)
        TapirEmailBase.register_email(MembershipConfirmationForInvestingMemberEmail)
        TapirEmailBase.register_email(TapirAccountCreatedEmail)
        TapirEmailBase.register_email(CoPurchaserUpdatedMail)
        TapirEmailBase.register_email(MembershipResignationConfirmation)
        TapirEmailBase.register_email(MembershipResignationTransferedSharesConfirmation)
