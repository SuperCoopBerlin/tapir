from django.test import RequestFactory

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import DraftUser, LogEntry
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.log.views import LogTable
from tapir.utils.expection_utils import TapirException
from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.utils.user_utils import UserUtils


class TestLogTableRenderMember(TapirFactoryTestBase):

    def setUp(self):
        super().setUp()
        self.user = self.login_as_member_office_user()
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get("/")
        self.request.user = self.user

    def _create_table(self, queryset):
        table = LogTable(data=queryset)
        table.before_render(self.request)
        return table

    def test_renderMember_tapirUser_isRendered(self):
        tapir_user = TapirUserFactory.create()
        log_entry = LogEntry.objects.create(
            actor=self.user,
            user=tapir_user,
        )
        queryset = LogEntry.objects.filter(pk=log_entry.pk)
        table = self._create_table(queryset)

        result = table.render_member(log_entry)

        self.assertIn(
            tapir_user.get_display_name(UserUtils.DISPLAY_NAME_TYPE_FULL), result
        )

    def test_renderMember_shareowner_isRendered(self):
        share_owner = ShareOwnerFactory.create()
        log_entry = LogEntry.objects.create(
            actor=self.user,
            share_owner=share_owner,
        )
        queryset = LogEntry.objects.filter(pk=log_entry.pk)
        table = self._create_table(queryset)

        result = table.render_member(log_entry)

        self.assertIn(
            share_owner.get_display_name(UserUtils.DISPLAY_NAME_TYPE_FULL), result
        )

    def test_renderMember_draftuser_isRendered(self):
        draft_user = DraftUser.objects.create(
            first_name="Max",
            last_name="Mustermann",
            email="draft@example.com",
        )
        log_entry = LogEntry.objects.create(
            actor=self.user,
            draft_user=draft_user,
        )
        queryset = LogEntry.objects.filter(pk=log_entry.pk)
        table = self._create_table(queryset)

        result = table.render_member(log_entry)

        self.assertIn(
            draft_user.get_display_name(UserUtils.DISPLAY_NAME_TYPE_FULL), result
        )

    def test_renderMember_noUser_throwsException(self):
        log_entry = LogEntry.objects.create(actor=self.user)
        queryset = LogEntry.objects.filter(pk=log_entry.pk)
        table = self._create_table(queryset)

        with self.assertRaises(TapirException):
            table.render_member(log_entry)
