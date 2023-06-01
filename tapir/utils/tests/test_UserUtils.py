from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.tests.factories import ShareOwnerFactory, DraftUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.utils.user_utils import UserUtils


class TestUserUtilsBuildDisplayName(TapirFactoryTestBase):
    FIRST_NAME = "John"
    USAGE_NAME = "Jane"
    LAST_NAME = "Doe"

    def test_personHasNoUsageName_displayFirstName(self):
        tapir_user = TapirUserFactory.build(first_name=self.FIRST_NAME, usage_name=None)
        display_name = UserUtils.build_display_name(
            tapir_user, UserUtils.DISPLAY_NAME_TYPE_SHORT
        )
        self.assertIn(self.FIRST_NAME, display_name)
        self.assertNotIn(self.USAGE_NAME, display_name)

    def test_personHasUsageName_displayUsageName(self):
        tapir_user = TapirUserFactory.build(
            first_name=self.FIRST_NAME, usage_name=self.USAGE_NAME
        )
        display_name = UserUtils.build_display_name(
            tapir_user, UserUtils.DISPLAY_NAME_TYPE_SHORT
        )
        self.assertIn(self.USAGE_NAME, display_name)
        self.assertNotIn(self.FIRST_NAME, display_name)

    def test_displayTypeShort_lastNameAndMemberNumberNotDisplayed(self):
        tapir_user = TapirUserFactory.build(
            last_name=self.LAST_NAME, share_owner__id=12
        )
        display_name = UserUtils.build_display_name(
            tapir_user, UserUtils.DISPLAY_NAME_TYPE_SHORT
        )
        self.assertNotIn(self.LAST_NAME, display_name)
        self.assertNotIn("12", display_name)

    def test_displayTypeLong_lastNameAndMemberNumberDisplayed(self):
        tapir_user = TapirUserFactory.build(
            last_name=self.LAST_NAME, share_owner__id=12
        )
        display_name = UserUtils.build_display_name(
            tapir_user, UserUtils.DISPLAY_NAME_TYPE_FULL
        )
        self.assertIn(self.LAST_NAME, display_name)
        self.assertIn("12", display_name)

    def test_tapirUser_displayIsCorrect(self):
        tapir_user = TapirUserFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
            share_owner__id=12,
        )
        display_name = UserUtils.build_display_name(
            tapir_user, UserUtils.DISPLAY_NAME_TYPE_FULL
        )
        self.assertEqual("Jane Doe #12", display_name)

    def test_shareOwner_displayIsCorrect(self):
        share_owner = ShareOwnerFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
            id=12,
        )
        display_name = UserUtils.build_display_name(
            share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL
        )
        self.assertEqual("Jane Doe #12", display_name)

    def test_draftUser_displayIsCorrect(self):
        draft_user = DraftUserFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
        )
        display_name = UserUtils.build_display_name(
            draft_user, UserUtils.DISPLAY_NAME_TYPE_FULL
        )
        self.assertEqual("Jane Doe", display_name)

    def test_shortCompanyName_companyNameIsUsed(self):
        share_owner = ShareOwnerFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
            company_name="SuperCoop",
            is_company=True,
        )
        display_name = UserUtils.build_display_name(
            share_owner, UserUtils.DISPLAY_NAME_TYPE_SHORT
        )
        self.assertEqual("SuperCoop", display_name)

    def test_fullCompanyName_companyNameIsUsed(self):
        share_owner = ShareOwnerFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
            company_name="SuperCoop",
            is_company=True,
            id=22,
        )
        display_name = UserUtils.build_display_name(
            share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL
        )
        self.assertEqual("SuperCoop #22", display_name)

    def test_legalName_displayIsCorrect(self):
        share_owner = ShareOwnerFactory.build(
            first_name=self.FIRST_NAME,
            usage_name=self.USAGE_NAME,
            last_name=self.LAST_NAME,
            company_name="SuperCoop",
            is_company=True,
            id=22,
        )
        display_name = UserUtils.build_display_name_legal(share_owner)
        self.assertEqual("John Doe", display_name)
