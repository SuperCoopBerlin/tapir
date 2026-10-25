import datetime

from django.core import mail
from django.urls import reverse
from rest_framework import status

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.emails.teamleader_page_updated_email import TeamleaderPageUpdatedEmail
from tapir.shifts.models import (
    Capability,
    CapabilityTranslation,
    TeamleaderPageContent,
    TeamleaderPageContentStatus,
)
from tapir.utils.tests_utils import (
    TapirEmailTestMixin,
    TapirFactoryTestBase,
    mock_timezone_now,
)


class TestTeamleaderPage(TapirEmailTestMixin, TapirFactoryTestBase):
    def test_get_loggedInAsNormalUser_returns403(self):
        self.login_as_normal_user()

        response = self.client.get(reverse("shifts:teamleader_page_edit"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_get_loggedInAsMemberOffice_returns403(self):
        self.login_as_member_office_user()

        response = self.client.get(reverse("shifts:teamleader_page_edit"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_get_loggedInAsEmployee_returns200(self):
        self.login_as_employee()

        response = self.client.get(reverse("shifts:teamleader_page_edit"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )

    def test_get_loggedInAsVorstand_returns200(self):
        self.login_as_vorstand()

        response = self.client.get(reverse("shifts:teamleader_page_edit"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_200_OK
        )

    def test_get_loggedInAsNormalMemberWithTeamleaderQualification_returns403(self):
        user = self.login_as_normal_user()
        user.shift_user_data.capabilities.set(
            [CapabilityTranslation.objects.get(name="Teamleader").capability]
        )
        user.shift_user_data.save()

        response = self.client.get(reverse("shifts:teamleader_page_edit"))

        self.assertStatusCode(
            response=response, expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_post_saveDraftOnly_savesDraftAndDontUpdateLive(self):
        logged_in_user = self.login_as_vorstand()
        other_user = TapirUserFactory.create()
        now = mock_timezone_now(
            test=self, now=datetime.datetime(year=2012, month=3, day=4)
        )

        live = TeamleaderPageContent.objects.create(
            content="LIVE",
            updated_by=other_user,
            status=TeamleaderPageContentStatus.LIVE,
        )
        draft = TeamleaderPageContent.objects.create(
            content="DRAFT_BEFORE",
            updated_by=other_user,
            status=TeamleaderPageContentStatus.DRAFT,
        )

        response = self.client.post(
            reverse("shifts:teamleader_page_edit"),
            data={"draft_content": "DRAFT_AFTER", "save_draft": True},
        )

        self.assertRedirects(
            response, expected_url=reverse("shifts:teamleader_page_edit")
        )

        live.refresh_from_db()
        self.assertEqual("LIVE", live.content)
        self.assertEqual(other_user, live.updated_by)

        draft.refresh_from_db()
        self.assertEqual("DRAFT_AFTER", draft.content)
        self.assertEqual(logged_in_user, draft.updated_by)
        self.assertEqual(now, draft.updated_on)

        self.assertEqual(0, len(mail.outbox))

    def _create_user_with_capabilities(self, capabilities: list[Capability]):
        user = TapirUserFactory.create()
        user.shift_user_data.capabilities.set(capabilities)
        user.shift_user_data.save()
        return user

    def test_post_publish_savesToBothLiveAndDraftAndSendMailsToTeamleaders(self):
        logged_in_user = self.login_as_vorstand()
        other_user = TapirUserFactory.create()

        teamleader_1 = self._create_user_with_capabilities(
            [CapabilityTranslation.objects.get(name="Teamleader").capability]
        )
        teamleader_2 = self._create_user_with_capabilities(
            [
                CapabilityTranslation.objects.get(name="Teamleader").capability,
                CapabilityTranslation.objects.get(name="Cashier").capability,
            ]
        )
        self._create_user_with_capabilities(
            [CapabilityTranslation.objects.get(name="Cashier").capability]
        )

        now = mock_timezone_now(
            test=self, now=datetime.datetime(year=2012, month=3, day=4)
        )

        live = TeamleaderPageContent.objects.create(
            content="LIVE_BEFORE",
            updated_by=other_user,
            status=TeamleaderPageContentStatus.LIVE,
        )
        draft = TeamleaderPageContent.objects.create(
            content="DRAFT_BEFORE",
            updated_by=other_user,
            status=TeamleaderPageContentStatus.DRAFT,
        )

        response = self.client.post(
            reverse("shifts:teamleader_page_edit"),
            data={"draft_content": "NEW_CONTENT", "publish": True},
        )

        self.assertRedirects(
            response, expected_url=reverse("shifts:teamleader_page_edit")
        )

        live.refresh_from_db()
        self.assertEqual("NEW_CONTENT", live.content)
        self.assertEqual(logged_in_user, live.updated_by)
        self.assertEqual(now, live.updated_on)

        draft.refresh_from_db()
        self.assertEqual("NEW_CONTENT", draft.content)
        self.assertEqual(logged_in_user, draft.updated_by)
        self.assertEqual(now, draft.updated_on)

        self.assertEqual(2, len(mail.outbox))
        for email in mail.outbox:
            if email.to == [teamleader_1.email]:
                self.assertEmailOfClass_GotSentTo(
                    expected_class=TeamleaderPageUpdatedEmail,
                    mail=email,
                    target_email_address=teamleader_1.email,
                )
            elif email.to == [teamleader_2.email]:
                self.assertEmailOfClass_GotSentTo(
                    expected_class=TeamleaderPageUpdatedEmail,
                    mail=email,
                    target_email_address=teamleader_2.email,
                )
            else:
                self.fail(f"Mail sent to user that should not get it: {email.to}")
