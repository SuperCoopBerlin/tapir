import datetime

from django.urls import reverse
from rest_framework import status

from tapir.shifts.models import (
    CapabilityTranslation,
    TeamleaderPageContent,
    TeamleaderPageContentStatus,
)
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestTeamleaderPage(TapirFactoryTestBase):
    def test_get_loggedInAsNormalUser_returns403(self):
        self.login_as_normal_user()

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_get_loggedInAsMemberOffice_returns403(self):
        self.login_as_member_office_user()

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_get_loggedInAsEmployee_returns200(self):
        self.login_as_employee()

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )

    def test_get_loggedInAsVorstand_returns200(self):
        self.login_as_vorstand()

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )

    def test_get_loggedInAsNormalMemberWithTeamleaderQualification_returns200(self):
        user = self.login_as_normal_user()
        user.shift_user_data.capabilities.set(
            [CapabilityTranslation.objects.get(name="Teamleader").capability]
        )
        user.shift_user_data.save()

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )

    def test_get_default_hasCorrectContextData(self):
        user = self.login_as_vorstand()
        updated_on = datetime.datetime(
            year=2028, month=11, day=29, hour=5, minute=22, tzinfo=datetime.UTC
        )
        TeamleaderPageContent.objects.create(
            content="LIVE_CONTENT",
            updated_by=user,
            status=TeamleaderPageContentStatus.LIVE,
        )
        TeamleaderPageContent.objects.update(updated_on=updated_on)
        TeamleaderPageContent.objects.create(
            content="DRAFT_CONTENT",
            updated_by=user,
            status=TeamleaderPageContentStatus.DRAFT,
        )

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )
        self.assertEqual("LIVE_CONTENT", response.context_data["page_content"])
        self.assertEqual(updated_on, response.context_data["updated_on"])

    def test_get_noLiveContent_hasPlaceholderContextData(self):
        user = self.login_as_vorstand()
        TeamleaderPageContent.objects.create(
            content="DRAFT_CONTENT",
            updated_by=user,
            status=TeamleaderPageContentStatus.DRAFT,
        )

        response = self.client.get(reverse("shifts:teamleader_page"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )
        self.assertEqual(
            "No content published yet", response.context_data["page_content"]
        )
