import datetime

from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.shifts.models import UpdateShiftUserDataLogEntry, ShiftUserData
from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestShiftPartnerHistoryService(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2022, month=7, day=13, hour=12)
    REFERENCE_TIME = timezone.make_aware(
        datetime.datetime(year=2022, month=5, day=21, hour=15)
    )

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    @staticmethod
    def create_irrelevant_log_entry(tapir_user, reference_time):
        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=tapir_user,
            old_values={"is_frozen": False},
            new_values={"is_frozen": True},
        )
        log_entry.created_date = reference_time - datetime.timedelta(hours=5)
        log_entry.save()

    def test_annotateShiftUserDataQuerysetWithHasShiftPartnerAtDate_noRelevantLogEntriesAndMemberHasShiftPartner_annotatesTrue(
        self,
    ):
        member_with_partner = TapirUserFactory.create()
        member_that_is_partner_of = TapirUserFactory.create()
        member_with_partner.shift_user_data.shift_partner = (
            member_that_is_partner_of.shift_user_data
        )
        member_with_partner.shift_user_data.save()

        self.create_irrelevant_log_entry(member_with_partner, self.REFERENCE_TIME)

        queryset = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            ShiftUserData.objects.all(),
            self.REFERENCE_TIME,
        )

        self.assertTrue(
            getattr(
                queryset.get(user=member_with_partner),
                ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER,
            )
        )
        self.assertFalse(
            getattr(
                queryset.get(user=member_that_is_partner_of),
                ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER,
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(user=member_with_partner),
                ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER_DATE_CHECK,
            ),
        )

    def test_annotateShiftUserDataQuerysetWithHasShiftPartnerAtDate_noRelevantLogEntriesAndMemberHasNoShiftPartner_annotatesFalse(
        self,
    ):
        member_with_partner = TapirUserFactory.create()
        self.create_irrelevant_log_entry(member_with_partner, self.REFERENCE_TIME)

        queryset = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            ShiftUserData.objects.all(), self.REFERENCE_TIME
        )

        self.assertFalse(
            getattr(
                queryset.get(), ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER
            )
        )
        self.assertEqual(
            self.REFERENCE_TIME,
            getattr(
                queryset.get(),
                ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER_DATE_CHECK,
            ),
        )

    def test_annotateShiftUserDataQuerysetWithHasShiftPartnerAtDate_hasRelevantLogEntriesWithShiftPartner_annotatesTrue(
        self,
    ):
        member_with_partner = TapirUserFactory.create()
        self.create_irrelevant_log_entry(member_with_partner, self.REFERENCE_TIME)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=member_with_partner,
            old_values={"shift_partner": 120},
            new_values={"shift_partner": None},
        )
        log_entry.created_date = self.REFERENCE_TIME + datetime.timedelta(hours=5)
        log_entry.save()

        queryset = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            ShiftUserData.objects.all(), self.REFERENCE_TIME
        )

        self.assertTrue(
            getattr(
                queryset.get(), ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER
            )
        )

    def test_annotateShiftUserDataQuerysetWithHasShiftPartnerAtDate_hasRelevantLogEntriesWithNoShiftPartner_annotatesFalse(
        self,
    ):
        member_with_partner = TapirUserFactory.create()
        member_that_is_partner_of = TapirUserFactory.create()
        member_with_partner.shift_user_data.shift_partner = (
            member_that_is_partner_of.shift_user_data
        )
        member_with_partner.shift_user_data.save()
        self.create_irrelevant_log_entry(member_with_partner, self.REFERENCE_TIME)

        log_entry = UpdateShiftUserDataLogEntry.objects.create(
            user=member_with_partner,
            old_values={"shift_partner": None},
            new_values={"shift_partner": 120},
        )
        log_entry.created_date = self.REFERENCE_TIME + datetime.timedelta(hours=5)
        log_entry.save()

        queryset = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            ShiftUserData.objects.all(), self.REFERENCE_TIME
        )

        self.assertFalse(
            getattr(
                queryset.get(user=member_with_partner),
                ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER,
            )
        )
