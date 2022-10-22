from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups
from tapir.settings import PERMISSION_COOP_MANAGE, PERMISSION_WELCOMEDESK_VIEW


class CoopConfig(AppConfig):
    name = "tapir.coop"

    def ready(self):
        self.register_sidebar_link_groups()
        self.register_emails()

    @staticmethod
    def register_sidebar_link_groups():
        coop_group = sidebar_link_groups.get_group(_("Cooperative"), 1)

        coop_group.add_link(
            display_name=_("Applicants"),
            material_icon="person_outline",
            url=reverse_lazy("coop:draftuser_list"),
            ordering=1,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        coop_group.add_link(
            display_name=_("Members"),
            material_icon="person",
            url=reverse_lazy("coop:shareowner_list"),
            ordering=2,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        coop_group.add_link(
            display_name=_("Matching program"),
            material_icon="card_giftcard",
            url=reverse_lazy("coop:matching_program_list"),
            ordering=3,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        coop_group.add_link(
            display_name=_("Incoming payments"),
            material_icon="euro",
            url=reverse_lazy("coop:incoming_payment_list"),
            ordering=4,
            required_permissions=[PERMISSION_COOP_MANAGE],
        )

        welcomedesk_group = sidebar_link_groups.get_group(_("Welcome Desk"), 2)

        welcomedesk_group.add_link(
            display_name=_("Welcome Desk"),
            material_icon="table_restaurant",
            url=reverse_lazy("coop:welcome_desk_search"),
            ordering=1,
            required_permissions=[PERMISSION_WELCOMEDESK_VIEW],
            html_id="welcome_desk_link",
        )

        misc_group = sidebar_link_groups.get_group(_("Miscellaneous"))

        misc_group.add_link(
            display_name=_("Coop statistics"),
            material_icon="calculate",
            url=reverse_lazy("coop:statistics"),
            ordering=5,
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

        TapirEmailBase.register_email(ExtraSharesConfirmationEmail)
        TapirEmailBase.register_email(MembershipConfirmationForActiveMemberEmail)
        TapirEmailBase.register_email(MembershipConfirmationForInvestingMemberEmail)
        TapirEmailBase.register_email(TapirAccountCreatedEmail)
