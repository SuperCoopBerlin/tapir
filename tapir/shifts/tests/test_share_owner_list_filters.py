from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.coop.tests.test_share_owner_list_filters import ShareOwnerFilterTestBase


class TestShareOwnerListShiftFilters(ShareOwnerFilterTestBase):
    @staticmethod
    def create_users_for_shift_partner_tests():
        users_with_partners = []
        users_that_are_partners_of = []
        for _ in range(2):
            user_with_partner: TapirUser = TapirUserFactory.create()
            user_that_is_partner_of = TapirUserFactory.create()
            user_with_partner.shift_user_data.shift_partner = (
                user_that_is_partner_of.shift_user_data
            )
            user_with_partner.shift_user_data.save()
            users_with_partners.append(user_with_partner.share_owner)
            users_that_are_partners_of.append(user_that_is_partner_of.share_owner)

        users_without_partners = [
            TapirUserFactory.create().share_owner,
            ShareOwnerFactory.create(),
        ]

        return [users_with_partners, users_that_are_partners_of, users_without_partners]

    def test_hasShiftPartner_default_showsCorrectList(self):
        [users_with_partners, users_that_are_partners_of, users_without_partners] = (
            self.create_users_for_shift_partner_tests()
        )

        self.visit_view(
            {"has_shift_partner": True},
            must_be_in=users_with_partners,
            must_be_out=users_without_partners + users_that_are_partners_of,
        )
        self.visit_view(
            {"has_shift_partner": False},
            must_be_in=users_without_partners + users_that_are_partners_of,
            must_be_out=users_with_partners,
        )

    def test_isShiftPartnerOf_default_showsCorrectList(self):
        [users_with_partners, users_that_are_partners_of, users_without_partners] = (
            self.create_users_for_shift_partner_tests()
        )

        self.visit_view(
            {"is_shift_partner_of": True},
            must_be_in=users_that_are_partners_of,
            must_be_out=users_with_partners + users_without_partners,
        )
        self.visit_view(
            {"is_shift_partner_of": False},
            must_be_in=users_with_partners + users_without_partners,
            must_be_out=users_that_are_partners_of,
        )
