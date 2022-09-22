import datetime

from django.urls import reverse
from django.utils import timezone

from tapir.coop.models import (
    UpdateShareOwnershipLogEntry,
    ShareOwnership,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestShareOwnership(TapirFactoryTestBase):
    def test_edit_requires_permissions(self):
        user = self.login_as_normal_user()
        response = self.client.get(
            reverse(
                "coop:share_update", args=[user.share_owner.share_ownerships.first().id]
            )
        )
        self.assertEqual(
            response.status_code,
            403,
            "A normal user should not be able to edit shares.",
        )

    def test_edit_creates_log_entry(self):
        user = self.login_as_member_office_user()
        self.assertEqual(UpdateShareOwnershipLogEntry.objects.count(), 0)

        share_ownership: ShareOwnership = user.share_owner.share_ownerships.first()
        end_date = timezone.now().date() + datetime.timedelta(days=100)
        response = self.client.post(
            reverse("coop:share_update", args=[share_ownership.id]),
            {
                "start_date": share_ownership.start_date,
                "end_date": end_date,
                "amount_paid": share_ownership.amount_paid,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UpdateShareOwnershipLogEntry.objects.count(), 1)
