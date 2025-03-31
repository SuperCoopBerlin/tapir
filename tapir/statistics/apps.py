from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.core.config import sidebar_link_groups


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tapir.statistics"

    def ready(self):
        super().ready()

        misc_group = sidebar_link_groups.get_group(_("Miscellaneous"), 5)

        misc_group.add_link(
            display_name=_("Statistics"),
            material_icon="calculate",
            url=reverse("statistics:main_statistics"),
            ordering=1,
        )

        self.register_data_providers()

    @classmethod
    def register_data_providers(cls):
        from tapir.statistics.services.data_providers.data_provider_abcd_members import (
            DataProviderAbcdMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_active_members import (
            DataProviderActiveMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_active_members_with_account import (
            DataProviderActiveMembersWithAccount,
        )
        from tapir.statistics.services.data_providers.data_provider_co_purchasers import (
            DataProviderCoPurchasers,
        )
        from tapir.statistics.services.data_providers.data_provider_exempted_members import (
            DataProviderExemptedMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_exempted_members_that_work import (
            DataProviderExemptedMembersThatWork,
        )
        from tapir.statistics.services.data_providers.data_provider_flying_members import (
            DataProviderFlyingMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_frozen_members import (
            DataProviderFrozenMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_frozen_members_long_term import (
            DataProviderFrozenMembersLongTerm,
        )
        from tapir.statistics.services.data_providers.data_provider_investing_members import (
            DataProviderInvestingMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_paused_members import (
            DataProviderPausedMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_purchasing_members import (
            DataProviderPurchasingMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_resignations_created import (
            DataProviderResignationsCreated,
        )
        from tapir.statistics.services.data_providers.data_provider_resignations_pending import (
            DataProviderResignationsPending,
        )
        from tapir.statistics.services.data_providers.data_provider_shift_partners import (
            DataProviderShiftPartners,
        )
        from tapir.statistics.services.data_providers.data_provider_total_members import (
            DataProviderTotalMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_working_members import (
            DataProviderWorkingMembers,
        )
        from tapir.statistics.services.data_providers.data_provider_payments_not_fully_paid import (
            DataProviderPaymentsNotFullyPaid,
        )
        from tapir.statistics.services.data_providers.data_provider_payments_paid_too_much import (
            DataProviderPaymentsPaidTooMuch,
        )
        from tapir.statistics.services.data_providers.data_provider_everyone import (
            DataProviderEveryone,
        )

        data_providers = [
            DataProviderAbcdMembers,
            DataProviderActiveMembers,
            DataProviderActiveMembersWithAccount,
            DataProviderCoPurchasers,
            DataProviderExemptedMembers,
            DataProviderExemptedMembersThatWork,
            DataProviderFlyingMembers,
            DataProviderFrozenMembers,
            DataProviderFrozenMembersLongTerm,
            DataProviderInvestingMembers,
            DataProviderPausedMembers,
            DataProviderPurchasingMembers,
            DataProviderResignationsCreated,
            DataProviderResignationsPending,
            DataProviderShiftPartners,
            DataProviderTotalMembers,
            DataProviderWorkingMembers,
            DataProviderPaymentsPaidTooMuch,
            DataProviderPaymentsNotFullyPaid,
            DataProviderEveryone,
        ]

        from tapir.statistics.services.data_providers.base_data_provider import (
            BaseDataProvider,
        )

        for data_provider in data_providers:
            BaseDataProvider.register_data_provider(data_provider)
