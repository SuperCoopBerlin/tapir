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
    ADMIN_MEMBER_NAME = "Skinner"

    admin_member: TapirUser
    normal_member_1: TapirUser
    normal_member_2: TapirUser
    normal_member_3: TapirUser

    def setUp(self) -> None:
        self.admin_member = TapirUserFactory.create(
            is_in_member_office=True, first_name=self.ADMIN_MEMBER_NAME
        )
        self.normal_member_1 = TapirUserFactory.create(
            is_in_member_office=False, first_name=self.NORMAL_MEMBER_1_NAME
        )
        self.normal_member_2 = TapirUserFactory.create(
            is_in_member_office=False, first_name=self.NORMAL_MEMBER_2_NAME
        )
        self.normal_member_3 = TapirUserFactory.create(
            is_in_member_office=False, first_name=self.NORMAL_MEMBER_3_NAME
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
        response = self.client.get(reverse("coop:incoming_payment_list"))
        self.assertEqual(response.status_code, 200)

        for payment in visible_payments:
            self.assert_payment_visible(response, payment)

        for payment in not_visible_payments:
            self.assert_payment_not_visible(response, payment)

    def test_normal_member_doesnt_see_other_peoples_names(self):
        self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
        self.create_incoming_payment(self.normal_member_2, self.normal_member_1),

        self.login_as_user(self.normal_member_1)
        response = self.client.get(reverse("coop:incoming_payment_list"))
        response_content = response.content.decode()

        self.assertIn(self.NORMAL_MEMBER_1_NAME, response_content)
        self.assertNotIn(self.NORMAL_MEMBER_2_NAME, response_content)
        self.assertNotIn(self.ADMIN_MEMBER_NAME, response_content)

    def test_admin_member_sees_all_names(self):
        self.create_incoming_payment(self.normal_member_1, self.normal_member_2),
        self.login_as_user(self.admin_member)
        response = self.client.get(reverse("coop:incoming_payment_list"))
        response_content = response.content.decode()

        self.assertIn(self.ADMIN_MEMBER_NAME, response_content)
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
            created_by=self.admin_member,
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

        self.login_as_user(self.admin_member)
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
