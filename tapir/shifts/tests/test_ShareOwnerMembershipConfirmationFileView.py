import datetime
from tempfile import SpooledTemporaryFile

from django.http import FileResponse
from django.urls import reverse
from pypdf import PdfReader

from tapir.coop.models import ShareOwnership
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestShareOwnerMembershipConfirmationFileView(TapirFactoryTestBase):
    VIEW_NAME_MEMBERSHIP_CONFIRMATION = "coop:shareowner_membership_confirmation"
    NOW = datetime.datetime(year=2021, month=5, day=12)

    def test_shareOwnerMembershipConfirmationFileView_loggedInAsNormalUser_notAuthorized(
        self,
    ):
        user = self.login_as_normal_user()
        response = self.client.get(
            reverse(
                self.VIEW_NAME_MEMBERSHIP_CONFIRMATION,
                args=[user.share_owner.id],
            )
        )
        self.assertEqual(
            403,
            response.status_code,
            "Normal users should not be allowed to access membership confirmation",
        )

    def test_shareOwnerMembershipConfirmationFileView_default_renders(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create()
        response = self.client.get(
            reverse(
                self.VIEW_NAME_MEMBERSHIP_CONFIRMATION,
                args=[share_owner.id],
            )
        )
        self.assertEqual(
            200,
            response.status_code,
            "Member office users should have access to membership confirmation",
        )

    def test_shareOwnerMembershipConfirmationFileView_noUrlParameters_fileContainsCurrentData(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=7, preferred_language="de")
        ShareOwnership.objects.update(
            start_date=self.NOW - datetime.timedelta(days=1), end_date=None
        )
        mock_timezone_now(self, self.NOW)

        response: FileResponse = self.client.get(
            reverse(
                self.VIEW_NAME_MEMBERSHIP_CONFIRMATION,
                args=[share_owner.id],
            )
        )
        self.assertEqual(200, response.status_code)

        text = self.get_text_from_pdf(response)
        self.assertIn("7 Anteil", text)
        self.assertIn("Berlin, 12. Mai 2021", text)

    def test_shareOwnerMembershipConfirmationFileView_withUrlParameters_fileContainsOverriddenData(
        self,
    ):
        self.login_as_member_office_user()
        share_owner = ShareOwnerFactory.create(nb_shares=7, preferred_language="de")
        ShareOwnership.objects.update(
            start_date=self.NOW - datetime.timedelta(days=1), end_date=None
        )
        mock_timezone_now(self, self.NOW)

        response: FileResponse = self.client.get(
            reverse(
                self.VIEW_NAME_MEMBERSHIP_CONFIRMATION,
                args=[share_owner.id],
            )
            + "?num_shares=3&date=27.3.2022"
        )
        self.assertEqual(200, response.status_code)

        text = self.get_text_from_pdf(response)
        self.assertIn("3 Anteil", text)
        self.assertIn("Berlin, 27. März 2022", text)

    def get_text_from_pdf(self, response):
        temp_file = SpooledTemporaryFile()
        temp_file.write(response.getvalue())

        reader = PdfReader(temp_file)
        self.assertEqual(1, len(reader.pages))
        page = reader.pages[0]
        return page.extract_text()
