from django.apps import AppConfig


class CoopConfig(AppConfig):
    name = "tapir.coop"

    def ready(self):
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

        TapirEmailBase.register_email(ExtraSharesConfirmationEmail)
        TapirEmailBase.register_email(MembershipConfirmationForActiveMemberEmail)
        TapirEmailBase.register_email(MembershipConfirmationForInvestingMemberEmail)
