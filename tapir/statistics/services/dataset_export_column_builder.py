import datetime
from decimal import Decimal

from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.payment_status_service import PaymentStatusService
from tapir.shifts.models import ShiftUserData, UpdateShiftUserDataLogEntry
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_exemption_service import ShiftExemptionService
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.utils.user_utils import UserUtils


class DatasetExportColumnBuilder:
    @staticmethod
    def build_column_member_number(share_owner: ShareOwner, **_):
        return share_owner.id

    @staticmethod
    def build_column_display_name(share_owner: ShareOwner, **_):
        return UserUtils.build_display_name(
            share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL
        )

    @staticmethod
    def build_column_is_company(share_owner: ShareOwner, **_):
        return share_owner.is_company

    @staticmethod
    def build_column_company_name(share_owner: ShareOwner, **_):
        return share_owner.company_name

    @staticmethod
    def build_column_first_name(share_owner: ShareOwner, **_):
        return share_owner.get_info().first_name

    @staticmethod
    def build_column_last_name(share_owner: ShareOwner, **_):
        return share_owner.get_info().last_name

    @staticmethod
    def build_column_usage_name(share_owner: ShareOwner, **_):
        return share_owner.get_info().usage_name

    @staticmethod
    def build_column_pronouns(share_owner: ShareOwner, **_):
        return share_owner.get_info().pronouns

    @staticmethod
    def build_column_email(share_owner: ShareOwner, **_):
        return share_owner.get_info().email

    @staticmethod
    def build_column_phone_number(share_owner: ShareOwner, **_):
        return share_owner.get_info().phone_number

    @staticmethod
    def build_column_birthdate(share_owner: ShareOwner, **_):
        return share_owner.get_info().birthdate

    @staticmethod
    def build_column_street(share_owner: ShareOwner, **_):
        return share_owner.get_info().street

    @staticmethod
    def build_column_street_2(share_owner: ShareOwner, **_):
        return share_owner.get_info().street_2

    @staticmethod
    def build_column_postcode(share_owner: ShareOwner, **_):
        return share_owner.get_info().postcode

    @staticmethod
    def build_column_city(share_owner: ShareOwner, **_):
        return share_owner.get_info().city

    @staticmethod
    def build_column_country(share_owner: ShareOwner, **_):
        return share_owner.get_info().country

    @staticmethod
    def build_column_preferred_language(share_owner: ShareOwner, **_):
        return share_owner.get_info().preferred_language

    @staticmethod
    def build_column_is_investing(share_owner: ShareOwner, **_):
        return share_owner.is_investing

    @staticmethod
    def build_column_ratenzahlung(share_owner: ShareOwner, **_):
        return share_owner.ratenzahlung

    @staticmethod
    def build_column_attended_welcome_session(share_owner: ShareOwner, **_):
        return share_owner.attended_welcome_session

    @staticmethod
    def build_column_co_purchaser(share_owner: ShareOwner, **_):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return ""
        return share_owner.user.co_purchaser

    @staticmethod
    def build_column_allows_purchase_tracking(share_owner: ShareOwner, **_):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return False
        return share_owner.user.allows_purchase_tracking

    @staticmethod
    def build_column_shift_capabilities(share_owner: ShareOwner, **_):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return ""
        return share_owner.user.shift_user_data.capabilities

    @staticmethod
    def build_column_shift_partner(share_owner: ShareOwner, **_):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return ""
        return UserUtils.build_display_name(
            share_owner.user.shift_user_data.shift_partner.user,
            UserUtils.DISPLAY_NAME_TYPE_FULL,
        )

    @staticmethod
    def build_column_shift_status(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        tapir_user = getattr(share_owner, "user", None)
        if (
            not tapir_user
            or not ShiftExpectationService.is_member_expected_to_do_shifts(
                share_owner.user.shift_user_data, reference_time
            )
        ):
            return "not working"
        return ShiftAttendanceModeService.get_attendance_mode(
            share_owner.user.shift_user_data, reference_time
        )

    @staticmethod
    def build_column_is_working(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return False
        return ShiftExpectationService.is_member_expected_to_do_shifts(
            share_owner.user.shift_user_data, reference_time
        )

    @staticmethod
    def build_column_is_exempted(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return False

        queryset = ShiftExemptionService.annotate_shift_user_data_queryset_with_has_exemption_at_date(
            ShiftUserData.objects.filter(id=share_owner.user.shift_user_data.id),
            reference_time,
        )
        return getattr(
            queryset.first(), ShiftExemptionService.ANNOTATION_HAS_EXEMPTION_AT_DATE
        )

    @staticmethod
    def build_column_is_paused(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        return MembershipPauseService.has_active_pause(share_owner, reference_time)

    @staticmethod
    def build_column_can_shop(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        return MemberCanShopService.can_shop(share_owner, reference_time)

    @staticmethod
    def build_column_currently_paid(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        annotated_share_owner = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.filter(id=share_owner.id), reference_time.date()
        ).get()
        return getattr(
            annotated_share_owner,
            PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
        )

    @staticmethod
    def build_column_expected_payment(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        annotated_share_owner = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.filter(id=share_owner.id), reference_time.date()
        ).get()
        return getattr(
            annotated_share_owner,
            PaymentStatusService.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE,
        )

    @staticmethod
    def build_column_payment_difference(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        annotated_share_owner = PaymentStatusService.annotate_with_payments_at_date(
            ShareOwner.objects.filter(id=share_owner.id), reference_time.date()
        ).get()
        return Decimal(
            getattr(
                annotated_share_owner,
                PaymentStatusService.ANNOTATION_CREDITED_PAYMENTS_SUM_AT_DATE,
            )
        ) - getattr(
            annotated_share_owner,
            PaymentStatusService.ANNOTATION_EXPECTED_PAYMENTS_SUM_AT_DATE,
        )

    @staticmethod
    def build_column_frozen_since(
        share_owner: ShareOwner, reference_time: datetime.datetime
    ):
        tapir_user = getattr(share_owner, "user", None)
        if not tapir_user:
            return None

        share_owner = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            ShareOwner.objects.filter(id=share_owner.id), reference_time
        ).first()
        is_frozen = getattr(
            share_owner, FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE
        )
        if not is_frozen:
            return None

        log_entry = (
            UpdateShiftUserDataLogEntry.objects.filter(
                user_id=tapir_user.id,
                created_date__lte=reference_time,
                new_values__has_key="is_frozen",
            )
            .order_by("-created_date")
            .first()
        )

        if not log_entry:
            return None

        return log_entry.created_date.date()
