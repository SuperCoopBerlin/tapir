from django.forms import HiddenInput
from django.template.response import TemplateResponse
from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.config import FEATURE_FLAG_SHIFT_PARTNER
from tapir.utils.tests_utils import TapirFactoryTestBase, FeatureFlagTestMixin


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
                "attendance_mode": member_2.shift_user_data.attendance_mode,
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
                "attendance_mode": member_3.shift_user_data.attendance_mode,
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
                "attendance_mode": member_3.shift_user_data.attendance_mode,
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
                "attendance_mode": member_1.shift_user_data.attendance_mode,
            },
        )
        self.assertRedirects(response, member_1.get_absolute_url())

        member_1.shift_user_data.refresh_from_db()
        self.assertEqual(
            member_2.shift_user_data, member_1.shift_user_data.shift_partner
        )
