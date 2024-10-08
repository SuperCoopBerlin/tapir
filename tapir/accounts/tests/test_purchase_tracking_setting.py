from pathlib import Path

from django.core.management import call_command
from django.urls import reverse

from tapir.accounts.management.commands.update_purchase_tracking_list import (
    Command as UpdatePurchaseTrackingListCommand,
)
from tapir.accounts.models import UpdateTapirUserLogEntry
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestPurchaseTrackingSetting(TapirFactoryTestBase):
    EXPORT_FILE = Path(UpdatePurchaseTrackingListCommand.FILE_NAME)

    def test_normal_user_can_update_their_own_setting(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        self.login_as_user(tapir_user)

        response = self.client.get(
            reverse(
                "accounts:update_purchase_tracking_allowed", args=[tapir_user.pk, 1]
            ),
        )

        self.assertRedirects(
            response=response, expected_url=tapir_user.get_absolute_url()
        )
        tapir_user.refresh_from_db()
        self.assertEqual(True, tapir_user.allows_purchase_tracking)

        self.assertEqual(1, UpdateTapirUserLogEntry.objects.count())
        log_entry = UpdateTapirUserLogEntry.objects.get(actor=tapir_user)
        self.assertEqual(tapir_user, log_entry.user)
        self.assertEqual(tapir_user, log_entry.actor)

    def test_other_user_cant_update_tracking_setting(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        self.login_as_member_office_user()

        response = self.client.get(
            reverse(
                "accounts:update_purchase_tracking_allowed", args=[tapir_user.pk, 1]
            ),
        )

        self.assertEqual(403, response.status_code)
        tapir_user.refresh_from_db()
        self.assertEqual(False, tapir_user.allows_purchase_tracking)

    def test_no_log_entry_created_if_setting_value_not_changed(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        self.login_as_user(tapir_user)

        self.client.get(
            reverse(
                "accounts:update_purchase_tracking_allowed", args=[tapir_user.pk, 0]
            ),
        )

        self.assertEqual(0, UpdateTapirUserLogEntry.objects.count())

    def test_updatePurchaseTrackingList_userHasTrackingEnabled_userIsInExportFile(self):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True)
        call_command("update_purchase_tracking_list")

        list_content = self.EXPORT_FILE.read_text()
        self.assertIn(tapir_user.last_name, list_content)
        self.EXPORT_FILE.unlink()

    def test_updatePurchaseTrackingList_userHasTrackingDisabled_userIsNotInExportFile(
        self,
    ):
        tapir_user = TapirUserFactory(allows_purchase_tracking=False)
        call_command("update_purchase_tracking_list")
        list_content = self.EXPORT_FILE.read_text()
        self.assertNotIn(tapir_user.last_name, list_content)
        self.EXPORT_FILE.unlink()

    def test_updatePurchaseTrackingList_userHasTrackingEnabledButNoShareOwner_userIsNotInExportFile(
        self,
    ):
        tapir_user = TapirUserFactory(allows_purchase_tracking=True, share_owner=None)
        call_command("update_purchase_tracking_list")
        list_content = self.EXPORT_FILE.read_text()
        self.assertNotIn(tapir_user.last_name, list_content)
        self.EXPORT_FILE.unlink()
