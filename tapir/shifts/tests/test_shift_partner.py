from django.forms import HiddenInput
from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.config import FEATURE_FLAG_SHIFT_PARTNER
from tapir.utils.tests_utils import TapirFactoryTestBase, FeatureFlagTestMixin
from django.utils import translation


class TestShiftPartner(FeatureFlagTestMixin, TapirFactoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.given_feature_flag_value(FEATURE_FLAG_SHIFT_PARTNER, True)

    def test_EditShiftUserDataView_featureFlagDisabled_shiftPartnerFieldNotShown(self):
        self.given_feature_flag_value(FEATURE_FLAG_SHIFT_PARTNER, False)

        tapir_user = self.login_as_member_office_user()
        response: TemplateResponse = self.client.get(
            reverse("shifts:edit_shift_user_data", args=[tapir_user.shift_user_data.id])
        )
        self.assertEqual(response.status_code, 200)

        shift_partner_field = response.context_data["form"].fields["shift_partner"]
        self.assertIsInstance(shift_partner_field.widget, HiddenInput)
        self.assertTrue(shift_partner_field.disabled)

    def test_EditShiftUserDataView_userIsAlreadyShiftPartnerOfSomeone_fieldIsDisabled(
        self,
    ):
        self.login_as_member_office_user()
        member_1 = TapirUserFactory.create()
        member_2 = TapirUserFactory.create()
        member_1.shift_user_data.shift_partner = member_2.shift_user_data
        member_1.shift_user_data.save()

        response: TemplateResponse = self.client.get(
            reverse("shifts:edit_shift_user_data", args=[member_2.shift_user_data.id])
        )
        self.assertEqual(response.status_code, 200)

        shift_partner_field = response.context_data["form"].fields["shift_partner"]
        self.assertTrue(shift_partner_field.disabled)

        # Try sending a shift partner update as if the field was enabled
        member_3 = TapirUserFactory.create()
        response: TemplateResponse = self.client.post(
            reverse("shifts:edit_shift_user_data", args=[member_2.shift_user_data.id]),
            data={
                "shift_partner": member_3.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        member_2.shift_user_data.refresh_from_db()
        self.assertEqual(None, member_2.shift_user_data.shift_partner)

    def test_EditShiftUserDataView_targetPartnerIsAlreadyShiftPartnerOfSomeone_formShowsError(
        self,
    ):
        self.login_as_member_office_user()
        member_1 = TapirUserFactory.create()
        member_2 = TapirUserFactory.create()
        member_1.shift_user_data.shift_partner = member_2.shift_user_data
        member_1.shift_user_data.save()
        member_3 = TapirUserFactory.create()

        response: TemplateResponse = self.client.post(
            reverse("shifts:edit_shift_user_data", args=[member_3.shift_user_data.id]),
            data={
                "shift_partner": member_2,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(1, len(response.context_data["form"].errors["shift_partner"]))
        member_3.shift_user_data.refresh_from_db()
        self.assertEqual(None, member_3.shift_user_data.shift_partner)

    def test_EditShiftUserDataView_targetPartnerAlreadyHasAPartner_formShowsError(
        self,
    ):
        self.login_as_member_office_user()
        member_1 = TapirUserFactory.create()
        member_2 = TapirUserFactory.create()
        member_1.shift_user_data.shift_partner = member_2.shift_user_data
        member_1.shift_user_data.save()
        member_3 = TapirUserFactory.create()

        response: TemplateResponse = self.client.post(
            reverse("shifts:edit_shift_user_data", args=[member_3.shift_user_data.id]),
            data={
                "shift_partner": member_1.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(1, len(response.context_data["form"].errors["shift_partner"]))
        member_3.shift_user_data.refresh_from_db()
        self.assertEqual(None, member_3.shift_user_data.shift_partner)

    def test_EditShiftUserDataView_default_partnerUpdated(
        self,
    ):
        self.login_as_member_office_user()
        member_1 = TapirUserFactory.create()
        member_2 = TapirUserFactory.create()

        response = self.client.post(
            reverse("shifts:edit_shift_user_data", args=[member_1.shift_user_data.id]),
            data={
                "shift_partner": member_2.id,
            },
        )
        self.assertRedirects(response, member_1.get_absolute_url())

        member_1.shift_user_data.refresh_from_db()
        self.assertEqual(
            member_2.shift_user_data, member_1.shift_user_data.shift_partner
        )

    def test_EditShiftUserDataView_memberAlreadyHasAPartner_initialValueOfFieldIsSet(
        self,
    ):
        self.login_as_member_office_user()
        member_1 = TapirUserFactory.create()
        member_2 = TapirUserFactory.create()
        member_1.shift_user_data.shift_partner = member_2.shift_user_data
        member_1.shift_user_data.save()

        response: TemplateResponse = self.client.get(
            reverse("shifts:edit_shift_user_data", args=[member_1.shift_user_data.id])
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(
            member_2.id,
            response.context_data["form"].initial["shift_partner"],
        )

    def test_EditShiftUserDataView_shiftPartnerIsNotInvesting_formErrorRaised(
        self,
    ):
        self.login_as_member_office_user()
        translation.activate("en")
        member = TapirUserFactory.create()
        shift_partner = TapirUserFactory.create(share_owner__is_investing=False)
        member.shift_user_data.shift_partner = shift_partner.shift_user_data
        member.shift_user_data.save()
        response = self.client.post(
            reverse("shifts:edit_shift_user_data", args=[member.shift_user_data.id]),
            data={
                "shift_partner": shift_partner.id,
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("shift_partner", response.context_data["form"].errors)
        self.assertIn(
            "The selected member must be an investing member.",
            response.context_data["form"].errors["shift_partner"],
        )

    def test_EditShiftUserDataView_memberIsInvesting_shiftPartnerFieldDisabled(self):
        self.login_as_member_office_user()
        member = TapirUserFactory.create(share_owner__is_investing=True)

        response = self.client.get(
            reverse("shifts:edit_shift_user_data", args=[member.shift_user_data.id])
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context_data["form"].fields["shift_partner"].disabled)
