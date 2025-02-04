import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import MembershipPause
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import ShiftUserCapability, ShiftExemption, ShiftAttendanceMode
from tapir.statistics.services.dataset_export_column_builder import (
    DatasetExportColumnBuilder,
)
from tapir.utils.tests_utils import (
    TapirFactoryTestBase,
    mock_timezone_now,
    create_member_that_is_working,
    create_member_that_can_shop,
)


class TestDatasetExportColumnBuilder(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2026, month=7, day=5, hour=17)
    REFERENCE_TIME = datetime.datetime(year=2025, month=2, day=8, hour=15)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)
        self.REFERENCE_TIME = timezone.make_aware(self.REFERENCE_TIME)

    def test_buildColumnMemberNumber_default_returnsMemberNumber(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_member_number(share_owner)

        self.assertEqual(share_owner.id, result)

    def test_buildColumnDisplayName_default_returnsDisplayName(self):
        share_owner = ShareOwnerFactory.create(
            first_name="Bruce", last_name="Wayne", usage_name="Batman"
        )

        result = DatasetExportColumnBuilder.build_column_display_name(share_owner)

        self.assertEqual(f"Batman Wayne #{share_owner.id}", result)

    def test_buildColumnIsCompany_default_returnsIsCompany(self):
        share_owner = ShareOwnerFactory.create(is_company=True)

        result = DatasetExportColumnBuilder.build_column_is_company(share_owner)

        self.assertTrue(result)

    def test_buildColumnFirstName_default_returnsFirstName(self):
        share_owner = ShareOwnerFactory.create(first_name="Bruce", usage_name="Batman")

        result = DatasetExportColumnBuilder.build_column_first_name(share_owner)

        self.assertEqual("Bruce", result)

    def test_buildColumnLastName_default_returnsFirstName(self):
        share_owner = ShareOwnerFactory.create(last_name="Wayne")

        result = DatasetExportColumnBuilder.build_column_last_name(share_owner)

        self.assertEqual("Wayne", result)

    def test_buildColumnUsageName_default_returnsUsageName(self):
        share_owner = ShareOwnerFactory.create(first_name="Bruce", usage_name="Batman")

        result = DatasetExportColumnBuilder.build_column_usage_name(share_owner)

        self.assertEqual("Batman", result)

    def test_buildColumnPronouns_default_returnsPronouns(self):
        share_owner = ShareOwnerFactory.create(pronouns="test pronouns")

        result = DatasetExportColumnBuilder.build_column_pronouns(share_owner)

        self.assertEqual("test pronouns", result)

    def test_buildColumnEmail_default_returnsEmail(self):
        share_owner = ShareOwnerFactory.create(email="test email")

        result = DatasetExportColumnBuilder.build_column_email(share_owner)

        self.assertEqual("test email", result)

    def test_buildColumnPhoneNumber_default_returnsPhoneNumber(self):
        share_owner = ShareOwnerFactory.create(phone_number="+4917612345678")

        result = DatasetExportColumnBuilder.build_column_phone_number(share_owner)

        self.assertEqual("+4917612345678", result)

    def test_buildColumnBirthdate_default_returnsBirthdate(self):
        birthdate = datetime.date(day=22, month=12, year=1990)
        share_owner = ShareOwnerFactory.create(birthdate=birthdate)

        result = DatasetExportColumnBuilder.build_column_birthdate(share_owner)

        self.assertEqual(birthdate, result)

    def test_buildColumnStreet_default_returnsStreet(self):
        share_owner = ShareOwnerFactory.create(street="test street")

        result = DatasetExportColumnBuilder.build_column_street(share_owner)

        self.assertEqual("test street", result)

    def test_buildColumnStreet2_default_returnsStreet2(self):
        share_owner = ShareOwnerFactory.create(street_2="test street 2")

        result = DatasetExportColumnBuilder.build_column_street_2(share_owner)

        self.assertEqual("test street 2", result)

    def test_buildColumnPostcode_default_returnsPostcode(self):
        share_owner = ShareOwnerFactory.create(postcode="13347")

        result = DatasetExportColumnBuilder.build_column_postcode(share_owner)

        self.assertEqual("13347", result)

    def test_buildColumnCity_default_returnsCity(self):
        share_owner = ShareOwnerFactory.create(city="test city")

        result = DatasetExportColumnBuilder.build_column_city(share_owner)

        self.assertEqual("test city", result)

    def test_buildColumnCountry_default_returnsCountry(self):
        share_owner = ShareOwnerFactory.create(country="FR")

        result = DatasetExportColumnBuilder.build_column_country(share_owner)

        self.assertEqual("FR", result)

    def test_buildColumnPreferredLanguage_default_returnsPreferredLanguage(self):
        share_owner = ShareOwnerFactory.create(preferred_language="DE")

        result = DatasetExportColumnBuilder.build_column_preferred_language(share_owner)

        self.assertEqual("DE", result)

    def test_buildColumnIsInvesting_default_returnsIsInvesting(self):
        share_owner = ShareOwnerFactory.create(is_investing=True)

        result = DatasetExportColumnBuilder.build_column_is_investing(share_owner)

        self.assertTrue(result)

    def test_buildColumnRatenzahlung_default_returnsRatenzahlung(self):
        share_owner = ShareOwnerFactory.create(ratenzahlung=True)

        result = DatasetExportColumnBuilder.build_column_ratenzahlung(share_owner)

        self.assertTrue(result)

    def test_buildColumnAttendedWelcomeSessions_default_returnsAttendedWelcomeSessions(
        self,
    ):
        share_owner = ShareOwnerFactory.create(attended_welcome_session=True)

        result = DatasetExportColumnBuilder.build_column_attended_welcome_session(
            share_owner
        )

        self.assertTrue(result)

    def test_buildColumnCoPurchaser_default_returnsCoPurchaser(self):
        share_owner = TapirUserFactory.create(
            co_purchaser="test co purchaser"
        ).share_owner

        result = DatasetExportColumnBuilder.build_column_co_purchaser(share_owner)

        self.assertEqual("test co purchaser", result)

    def test_buildColumnCoPurchaser_noAccount_returnsEmptyString(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_co_purchaser(share_owner)

        self.assertEqual("", result)

    def test_buildColumnAllowsPurchaseTracking_default_returnsAllowsPurchaseTracking(
        self,
    ):
        share_owner = TapirUserFactory.create(allows_purchase_tracking=True).share_owner

        result = DatasetExportColumnBuilder.build_column_allows_purchase_tracking(
            share_owner
        )

        self.assertTrue(result)

    def test_buildColumnAllowsPurchaseTracking_noAccount_returnsFalse(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_allows_purchase_tracking(
            share_owner
        )

        self.assertFalse(result)

    def test_buildColumnShiftCapabilities_default_returnsCapabilities(self):
        share_owner = TapirUserFactory.create(
            shift_capabilities=[ShiftUserCapability.BREAD_DELIVERY]
        ).share_owner

        result = DatasetExportColumnBuilder.build_column_shift_capabilities(share_owner)

        self.assertEqual([ShiftUserCapability.BREAD_DELIVERY], result)

    def test_buildColumnShiftCapabilities_noAccount_returnsEmptyString(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_shift_capabilities(share_owner)

        self.assertEqual("", result)

    def test_buildColumnShiftPartner_default_returnsShiftpartner(self):
        share_owner = TapirUserFactory.create().share_owner
        partner = TapirUserFactory.create(
            first_name="Frida", last_name="Kahlo", usage_name=""
        )
        share_owner.user.shift_user_data.shift_partner = partner.shift_user_data
        share_owner.user.shift_user_data.save()

        result = DatasetExportColumnBuilder.build_column_shift_partner(share_owner)

        self.assertEqual(f"Frida Kahlo #{partner.get_member_number()}", result)

    def test_buildColumnShiftPartner_noAccount_returnsEmptyString(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_shift_partner(share_owner)

        self.assertEqual("", result)

    def test_buildColumnShiftStatus_noAccount_returnsNotWorking(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_shift_status(
            share_owner, self.REFERENCE_TIME
        )

        self.assertEqual("not working", result)

    def test_buildColumnShiftStatus_memberIsExempted_returnsNotWorking(self):
        share_owner = create_member_that_is_working(self, self.NOW).share_owner
        ShiftExemption.objects.create(
            shift_user_data=share_owner.user.shift_user_data,
            description="test description",
            start_date=self.REFERENCE_TIME - datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME + datetime.timedelta(days=1),
        )

        result = DatasetExportColumnBuilder.build_column_shift_status(
            share_owner, self.REFERENCE_TIME
        )

        self.assertEqual("not working", result)

    def test_buildColumnShiftStatus_default_returnsStatus(self):
        share_owner = create_member_that_is_working(
            self, self.REFERENCE_TIME
        ).share_owner

        result = DatasetExportColumnBuilder.build_column_shift_status(
            share_owner, self.REFERENCE_TIME
        )

        self.assertEqual(ShiftAttendanceMode.FLYING, result)

    def test_buildColumnIsWorking_noAccount_returnsFalse(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_is_working(
            share_owner, self.REFERENCE_TIME
        )

        self.assertFalse(result)

    def test_buildColumnIsWorking_default_returnsIsWorking(self):
        share_owner = create_member_that_is_working(
            self, self.REFERENCE_TIME
        ).share_owner

        result = DatasetExportColumnBuilder.build_column_is_working(
            share_owner, self.REFERENCE_TIME
        )

        self.assertTrue(result)

    def test_buildColumnIsExempted_noAccount_returnsFalse(self):
        share_owner = ShareOwnerFactory.create()

        result = DatasetExportColumnBuilder.build_column_is_exempted(
            share_owner, self.REFERENCE_TIME
        )

        self.assertFalse(result)

    def test_buildColumnIsExempted_default_returnsIsExempted(self):
        share_owner = TapirUserFactory.create().share_owner
        ShiftExemption.objects.create(
            shift_user_data=share_owner.user.shift_user_data,
            description="test description",
            start_date=self.REFERENCE_TIME - datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME + datetime.timedelta(days=1),
        )

        result = DatasetExportColumnBuilder.build_column_is_exempted(
            share_owner, self.REFERENCE_TIME
        )

        self.assertTrue(result)

    def test_buildColumnIsPaused_default_returnsIsPaused(self):
        share_owner = TapirUserFactory.create().share_owner
        MembershipPause.objects.create(
            share_owner=share_owner,
            description="test description",
            start_date=self.REFERENCE_TIME - datetime.timedelta(days=1),
            end_date=self.REFERENCE_TIME + datetime.timedelta(days=1),
        )

        result = DatasetExportColumnBuilder.build_column_is_paused(
            share_owner, self.REFERENCE_TIME
        )

        self.assertTrue(result)

    def test_buildColumnCanShop_default_returnsCanShop(self):
        share_owner = create_member_that_can_shop(self, self.REFERENCE_TIME).share_owner

        result = DatasetExportColumnBuilder.build_column_can_shop(
            share_owner, self.REFERENCE_TIME
        )

        self.assertTrue(result)
