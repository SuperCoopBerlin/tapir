import datetime

from django.utils import timezone

from tapir.accounts.models import TapirUser, UpdateTapirUserLogEntry
from tapir.accounts.services.co_purchaser_history_service import (
    CoPurchaserHistoryService,
)
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now

from tapir.accounts.forms import TapirUserForm


class TestCoPurchaserHistoryService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2022, month=7, day=13, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=5, day=21, hour=15)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    @staticmethod
    def create_irrelevant_log_entry(tapir_user, reference_time):
        log_entry = UpdateTapirUserLogEntry.objects.create(
            user=tapir_user,
            old_values={"city": "Berlin"},
            new_values={"city": "Munich"},
        )
        log_entry.created_date = reference_time - datetime.timedelta(hours=5)
        log_entry.save()

    def test_annotateTapirUserQuerysetWithHasCoPurchaserAtDate_noRelevantLogEntriesAndMemberHasCoPurchaser_annotatesTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create(co_purchaser="A test co-purchaser")
        self.create_irrelevant_log_entry(tapir_user, self.REFERENCE_TIME)

        queryset = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            TapirUser.objects.all(), self.REFERENCE_TIME
        )

        self.assertEqual(
            "A test co-purchaser", getattr(queryset.get(), "co_purchaser_at_date")
        )
        self.assertTrue(
            getattr(
                queryset.get(), CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(),
                CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK,
            ),
        )

    def test_annotateTapirUserQuerysetWithHasCoPurchaserAtDate_noRelevantLogEntriesAndMemberHasNoCoPurchaser_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(co_purchaser="")
        self.create_irrelevant_log_entry(tapir_user, self.REFERENCE_TIME)

        queryset = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            TapirUser.objects.all(), self.REFERENCE_TIME
        )

        self.assertEqual("", getattr(queryset.get(), "co_purchaser_at_date"))
        self.assertFalse(
            getattr(
                queryset.get(), CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(),
                CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK,
            ),
        )

    def test_annotateTapirUserQuerysetWithHasCoPurchaserAtDate_hasRelevantLogEntriesWithCoPurchaser_annotatesTrue(
        self,
    ):
        tapir_user = TapirUserFactory.create(co_purchaser="")
        self.create_irrelevant_log_entry(tapir_user, self.REFERENCE_TIME)

        log_entry_in_the_past = UpdateTapirUserLogEntry.objects.create(
            user=tapir_user,
            old_values={"co_purchaser": ""},
            new_values={"co_purchaser": "Someone"},
        )
        log_entry_in_the_past.created_date = self.REFERENCE_TIME - datetime.timedelta(
            hours=5
        )
        log_entry_in_the_past.save()

        log_entry_in_the_future = UpdateTapirUserLogEntry.objects.create(
            user=tapir_user,
            old_values={"co_purchaser": "Someone"},
            new_values={"co_purchaser": ""},
        )
        log_entry_in_the_future.created_date = self.REFERENCE_TIME + datetime.timedelta(
            hours=5
        )
        log_entry_in_the_future.save()

        queryset = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            TapirUser.objects.all(), self.REFERENCE_TIME
        )

        self.assertEqual("Someone", getattr(queryset.get(), "co_purchaser_at_date"))
        self.assertTrue(
            getattr(
                queryset.get(), CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(),
                CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK,
            ),
        )

    def test_annotateTapirUserQuerysetWithHasCoPurchaserAtDate_hasRelevantLogEntriesWithNoCoPurchaser_annotatesFalse(
        self,
    ):
        tapir_user = TapirUserFactory.create(co_purchaser="Someone")
        self.create_irrelevant_log_entry(tapir_user, self.REFERENCE_TIME)

        log_entry_in_the_past = UpdateTapirUserLogEntry.objects.create(
            user=tapir_user,
            old_values={"co_purchaser": "Someone"},
            new_values={"co_purchaser": ""},
        )
        log_entry_in_the_past.created_date = self.REFERENCE_TIME - datetime.timedelta(
            hours=5
        )
        log_entry_in_the_past.save()

        log_entry_in_the_future = UpdateTapirUserLogEntry.objects.create(
            user=tapir_user,
            old_values={"co_purchaser": ""},
            new_values={"co_purchaser": "Someone"},
        )
        log_entry_in_the_future.created_date = self.REFERENCE_TIME + datetime.timedelta(
            hours=5
        )
        log_entry_in_the_future.save()

        queryset = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            TapirUser.objects.all(), self.REFERENCE_TIME
        )

        self.assertEqual("", getattr(queryset.get(), "co_purchaser_at_date"))
        self.assertFalse(
            getattr(
                queryset.get(), CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(),
                CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER_DATE_CHECK,
            ),
        )

    def test_TapirUserForm_hasCopurchaserDisabled_whenShareownerIsInvesting(self):
        tapir_user = TapirUserFactory.create()
        tapir_user.share_owner.is_investing = True
        tapir_user.share_owner.save()
        form = TapirUserForm(instance=tapir_user)
        self.assertTrue(form.fields["co_purchaser"].disabled)
