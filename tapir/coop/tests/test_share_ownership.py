import datetime

from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from tapir.coop.models import (
    UpdateShareOwnershipLogEntry,
    ShareOwnership,
    DeleteShareOwnershipLogEntry,
)
from tapir.coop.tests.factories import ShareOwnerFactory
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

    def test_ShareOwnershipUpdateView_default_contextDataIsCorrect(self):
        self.login_as_member_office_user(preferred_language="en")
        share_owner = ShareOwnerFactory.create(
            first_name="Hyper", usage_name="Super", last_name="Coop"
        )
        response: TemplateResponse = self.client.get(
            reverse("coop:share_update", args=[share_owner.share_ownerships.first().id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            f"Edit share: Super Coop #{share_owner.id}",
            response.context_data["page_title"],
        )
        self.assertEqual(
            f"Edit share: Super Coop #{share_owner.id}",
            strip_tags(response.context_data["card_title"]),
        )

    def test_shareOwnershipDelete_loggedInAsMemberOffice_notAuthorized(self):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=2)

        share_ownership: ShareOwnership = share_owner.share_ownerships.first()
        response: TemplateResponse = self.client.post(
            reverse("coop:shareownership_delete", args=[share_ownership.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(share_owner.share_ownerships.count(), 2)

    def test_shareOwnershipDelete_loggedInAsVorstand_shareDeleted(self):
        self.login_as_vorstand()
        share_owner = ShareOwnerFactory.create(nb_shares=2)

        share_ownership: ShareOwnership = share_owner.share_ownerships.first()
        response: TemplateResponse = self.client.post(
            reverse("coop:shareownership_delete", args=[share_ownership.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(share_owner.share_ownerships.count(), 1)

    def test_shareOwnershipDelete_loggedInAsMemberOffice_deleteButtonNotShown(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create()

        response: TemplateResponse = self.client.get(share_owner.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "share_ownership_delete_dropdown")

    def test_shareOwnershipDelete_loggedInAsVorstand_deleteButtonShown(
        self,
    ):
        self.login_as_vorstand()
        share_owner = ShareOwnerFactory.create()

        response: TemplateResponse = self.client.get(share_owner.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "share_ownership_delete_dropdown")

    def test_shareOwnershipDelete_default_logEntryCreated(self):
        vorstand_user = self.login_as_vorstand()
        share_owner = ShareOwnerFactory.create(nb_shares=1)

        self.assertEqual(0, DeleteShareOwnershipLogEntry.objects.count())
        share_ownership: ShareOwnership = share_owner.share_ownerships.first()
        response: TemplateResponse = self.client.post(
            reverse("coop:shareownership_delete", args=[share_ownership.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(share_owner.share_ownerships.count(), 0)
        self.assertEqual(1, DeleteShareOwnershipLogEntry.objects.count())
        log_entry = DeleteShareOwnershipLogEntry.objects.get()
        self.assertEqual(log_entry.actor, vorstand_user)
        self.assertEqual(log_entry.share_owner, share_owner)
        self.assertEqual(
            log_entry.values["start_date"],
            share_ownership.start_date.strftime("%Y-%m-%d"),
        )
