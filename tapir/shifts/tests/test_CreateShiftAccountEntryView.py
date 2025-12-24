import datetime

from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import strip_tags

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import ShiftAccountEntry
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCreateShiftAccountEntryView(TapirFactoryTestBase):
    VIEW_NAME = "shifts:create_shift_account_entry"

    def test_createShiftAccountEntryView_loggedInAsNormalUser_notAuthorized(self):
        tapir_user = self.login_as_normal_user()

        response = self.client.get(reverse(self.VIEW_NAME, args=[tapir_user.id]))

        self.assertEqual(403, response.status_code)

    def test_createShiftAccountEntryView_loggedInAsMemberOffice_contextDataIsCorrect(
        self,
    ):
        self.login_as_member_office_user(preferred_language="en")
        tapir_user: TapirUser = TapirUserFactory.create(
            first_name="Hyper", usage_name="Super", last_name="Coop"
        )

        response: TemplateResponse = self.client.get(
            reverse(self.VIEW_NAME, args=[tapir_user.id])
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            f"Shift account: Super Coop #{tapir_user.get_member_number()}",
            response.context_data["page_title"],
        )
        self.assertEqual(
            f"Create manual shift account entry for: Super Coop #{tapir_user.get_member_number()}",
            strip_tags(response.context_data["card_title"]),
        )

    def test_createShiftAccountEntryView_default_entryCreated(
        self,
    ):
        self.login_as_member_office_user()
        tapir_user: TapirUser = TapirUserFactory.create()

        response: TemplateResponse = self.client.post(
            reverse(self.VIEW_NAME, args=[tapir_user.id]),
            data={
                "value": -1,
                "date": datetime.date(year=2024, month=1, day=1),
                "description": "Test description",
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, ShiftAccountEntry.objects.count())
