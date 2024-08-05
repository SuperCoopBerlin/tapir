from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import (
    IncomingPayment,
    CreatePaymentLogEntry,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestIncomingPayments(TapirFactoryTestBase):
    NORMAL_MEMBER_1_NAME = "Bart"
    NORMAL_MEMBER_2_NAME = "Lisa"
    NORMAL_MEMBER_3_NAME = "Maggie"
    ACCOUNTING_TEAM_MEMBER_NAME = "Skinner"
    MEMBER_OFFICE_MEMBER_NAME = "Flanders"

    VIEW_NAME_PAYMENT_LIST = "coop:incoming_payment_list"

    accounting_team_member: TapirUser
    member_office_member: TapirUser
    normal_member_1: TapirUser
    normal_member_2: TapirUser
    normal_member_3: TapirUser

    def setUp(self) -> None:
        self.accounting_team_member = TapirUserFactory.create(
            is_in_accounting_team=True,
            is_in_member_office=False,
            first_name=self.ACCOUNTING_TEAM_MEMBER_NAME,
            usage_name="",
        )
        self.member_office_member = TapirUserFactory.create(
            is_in_accounting_team=False,
            is_in_member_office=True,
            first_name=self.MEMBER_OFFICE_MEMBER_NAME,
            usage_name="",
        )
        self.normal_member_1 = TapirUserFactory.create(
            is_in_accounting_team=False,
            is_in_member_office=False,
            first_name=self.NORMAL_MEMBER_1_NAME,
            usage_name="",
        )
        self.normal_member_2 = TapirUserFactory.create(
            is_in_accounting_team=False,
            is_in_member_office=False,
            first_name=self.NORMAL_MEMBER_2_NAME,
            usage_name="",
        )
        self.normal_member_3 = TapirUserFactory.create(
            is_in_accounting_team=False,
            is_in_member_office=False,
            first_name=self.NORMAL_MEMBER_3_NAME,
            usage_name="",
        )

    def test_normal_member_doesnt_see_other_peoples_payments(self):
        visible_payments = [
            self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
            self.create_incoming_payment(self.normal_member_2, self.normal_member_1),
            self.create_incoming_payment(self.normal_member_1, self.normal_member_1),
        ]
        not_visible_payments = [
            self.create_incoming_payment(self.normal_member_2, self.normal_member_2),
            self.create_incoming_payment(self.normal_member_2, self.normal_member_3),
        ]

        self.login_as_user(self.normal_member_1)
        response = self.client.get(reverse(self.VIEW_NAME_PAYMENT_LIST))
        self.assertEqual(response.status_code, 200)

        for payment in visible_payments:
            self.assert_payment_visible(response, payment)

        for payment in not_visible_payments:
            self.assert_payment_not_visible(response, payment)

    def test_normal_member_doesnt_see_other_peoples_names(self):
        self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
        self.create_incoming_payment(self.normal_member_2, self.normal_member_1),

        self.login_as_user(self.normal_member_1)
        response = self.client.get(reverse(self.VIEW_NAME_PAYMENT_LIST))
        response_content = response.content.decode()

        self.assertIn(self.NORMAL_MEMBER_1_NAME, response_content)
        self.assertNotIn(self.NORMAL_MEMBER_2_NAME, response_content)
        self.assertNotIn(self.ACCOUNTING_TEAM_MEMBER_NAME, response_content)

    def test_accounting_team_member_sees_all_names(self):
        self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
        self.login_as_user(self.accounting_team_member)
        self._assert_all_names_visible_in_payment_list_view()

    def test_member_office_team_member_sees_all_names(self):
        self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
        self.login_as_user(self.member_office_member)
        self._assert_all_names_visible_in_payment_list_view()

    def _assert_all_names_visible_in_payment_list_view(self):
        response = self.client.get(reverse(self.VIEW_NAME_PAYMENT_LIST))
        response_content = response.content.decode()

        self.assertIn(self.ACCOUNTING_TEAM_MEMBER_NAME, response_content)
        self.assertIn(self.NORMAL_MEMBER_1_NAME, response_content)
        self.assertIn(self.NORMAL_MEMBER_2_NAME, response_content)

    def create_incoming_payment(
        self, paying_member: TapirUser, credited_member: TapirUser
    ) -> IncomingPayment:
        return IncomingPayment.objects.create(
            paying_member=paying_member.share_owner,
            credited_member=credited_member.share_owner,
            amount=100,
            payment_date=timezone.now().date(),
            creation_date=timezone.now().date(),
            created_by=self.accounting_team_member,
        )

    def assert_payment_visible(self, response, payment):
        self.assertInHTML(
            f"<td>#{payment.id}</td>",
            response.content.decode(),
            1,
            "Payment should be visible because it concerns the logged in member.",
        )

    def assert_payment_not_visible(self, response, payment):
        self.assertNotIn(
            f"<td>#{payment.id}</td>",
            response.content.decode(),
            "Payment should not be visible because it does not concern the logged in member.",
        )

    def test_add_payment_creates_logentry(self):
        self.assertEqual(CreatePaymentLogEntry.objects.count(), 0)

        self.login_as_user(self.accounting_team_member)
        response = self.client.post(
            reverse("coop:incoming_payment_create"),
            {
                "paying_member": self.normal_member_1.share_owner.id,
                "credited_member": self.normal_member_1.share_owner.id,
                "amount": 100,
                "payment_date": timezone.now().date(),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(CreatePaymentLogEntry.objects.count(), 1)
        log_entry = CreatePaymentLogEntry.objects.first()
        self.assertEqual(log_entry.amount, 100)
        self.assertEqual(log_entry.payment_date, timezone.now().date())

    def test_member_office_cannot_create_payment(self):
        self.login_as_user(self.member_office_member)
        response = self.client.post(
            reverse("coop:incoming_payment_create"),
            {
                "paying_member": self.normal_member_1.share_owner.id,
                "credited_member": self.normal_member_1.share_owner.id,
                "amount": 100,
                "payment_date": timezone.now().date(),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 403)

    def test_incomingPaymentListView_loggedInAsAccounting_actionColumnNotShowing(self):
        accounting_team_member = TapirUserFactory.create(is_in_accounting_team=True)
        self.login_as_user(accounting_team_member)

        response: TemplateResponse = self.client.get(
            reverse("coop:incoming_payment_list")
        )

        self.assertNotIn("Actions", response.content.decode())

    def test_incomingPaymentListView_loggedInAsVorstand_actionColumnShowing(self):
        self.login_as_vorstand()

        response: TemplateResponse = self.client.get(
            reverse("coop:incoming_payment_list")
        )

        self.assertIn("Actions", response.content.decode())
