import datetime

from django.core import mail
from django.urls import reverse

from tapir import settings
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.management.commands.send_accounting_recap import (
    Command,
)
from tapir.coop.models import (
    NewMembershipsForAccountingRecap,
    ExtraSharesForAccountingRecap,
)
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase


class TestSendAccountingRecap(TapirFactoryTestBase, TapirEmailTestBase):
    VIEW_NAME = "coop:shareowner_membership_confirmation"

    def test_send_accounting_recap(self):
        member_1 = ShareOwnerFactory.create()
        NewMembershipsForAccountingRecap.objects.create(
            member=member_1,
            number_of_shares=3,
            date=datetime.date(day=12, month=1, year=2020),
        )
        member_2 = TapirUserFactory.create().share_owner
        NewMembershipsForAccountingRecap.objects.create(
            member=member_2,
            number_of_shares=2,
            date=datetime.date(day=15, month=4, year=2021),
        )

        member_3 = ShareOwnerFactory.create()
        ExtraSharesForAccountingRecap.objects.create(
            member=member_3,
            number_of_shares=5,
            date=datetime.date(day=12, month=3, year=2022),
        )
        member_4 = TapirUserFactory.create().share_owner
        ExtraSharesForAccountingRecap.objects.create(
            member=member_4,
            number_of_shares=4,
            date=datetime.date(day=16, month=10, year=2023),
        )

        self.assertEqual(0, len(mail.outbox))
        Command().handle()
        self.assertEqual(1, len(mail.outbox))
        sent_mail = mail.outbox[0]
        self.assertEqual([settings.EMAIL_ADDRESS_ACCOUNTING], sent_mail.to)

        self.assertIn(member_1.get_info().usage_name, sent_mail.body)
        url_member_1 = (
            reverse(self.VIEW_NAME, args=[member_1.pk])
            + "?num_shares=3&date=12.01.2020"
        )
        self.assertIn(url_member_1, sent_mail.body)

        self.assertIn(member_2.get_info().usage_name, sent_mail.body)
        url_member_2 = (
            reverse(self.VIEW_NAME, args=[member_2.pk])
            + "?num_shares=2&date=15.04.2021"
        )
        self.assertIn(url_member_2, sent_mail.body)

        self.assertIn(member_3.get_info().usage_name, sent_mail.body)
        url_member_3 = (
            reverse(self.VIEW_NAME, args=[member_3.pk])
            + "?num_shares=5&date=12.03.2022"
        )
        self.assertIn(url_member_3, sent_mail.body)

        self.assertIn(member_4.get_info().usage_name, sent_mail.body)
        url_member_4 = (
            reverse(self.VIEW_NAME, args=[member_4.pk])
            + "?num_shares=4&date=16.10.2023"
        )
        self.assertIn(url_member_4, sent_mail.body)

        self.assertEqual(0, NewMembershipsForAccountingRecap.objects.count())
        self.assertEqual(0, ExtraSharesForAccountingRecap.objects.count())
