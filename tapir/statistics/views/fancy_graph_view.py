import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner, MembershipResignation
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import (
    ShiftUserData,
)
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.statistics.views.fancy_graph.number_of_working_members_view import (
    NumberOfWorkingMembersAtDateView,
)

DATE_FORMAT = "%Y-%m-%d"


def get_shift_user_datas_of_working_members_annotated_with_attendance_mode(
    reference_time: datetime.datetime,
):
    reference_date = reference_time.date()

    shift_user_datas = (
        ShiftUserData.objects.filter(user__share_owner__isnull=False)
        .prefetch_related("user")
        .prefetch_related("user__share_owner")
        .prefetch_related("user__share_owner__share_ownerships")
        .prefetch_related("shift_exemptions")
    )
    shift_user_datas = FrozenStatusHistoryService.annotate_shift_user_data_queryset_with_is_frozen_at_datetime(
        shift_user_datas, reference_time
    )
    share_owners = (
        NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            ShareOwner.objects.all(), reference_date
        )
    )
    share_owners = (
        MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
            share_owners, reference_date
        )
    )
    share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
        share_owners, reference_time
    )
    share_owners = {share_owner.id: share_owner for share_owner in share_owners}
    for shift_user_data in shift_user_datas:
        NumberOfWorkingMembersAtDateView.transfer_attributes(
            share_owners[shift_user_data.user.share_owner.id],
            shift_user_data.user.share_owner,
            [
                NumberOfSharesService.ANNOTATION_NUMBER_OF_ACTIVE_SHARES,
                NumberOfSharesService.ANNOTATION_SHARES_ACTIVE_AT_DATE,
                MembershipPauseService.ANNOTATION_HAS_ACTIVE_PAUSE,
                MembershipPauseService.ANNOTATION_HAS_ACTIVE_PAUSE_AT_DATE,
                InvestingStatusService.ANNOTATION_WAS_INVESTING,
                InvestingStatusService.ANNOTATION_WAS_INVESTING_AT_DATE,
            ],
        )

    ids_of_suds_of_members_that_do_shifts = [
        shift_user_data.id
        for shift_user_data in shift_user_datas
        if ShiftExpectationService.is_member_expected_to_do_shifts(
            shift_user_data, reference_time
        )
    ]

    shift_user_datas = ShiftUserData.objects.filter(
        id__in=ids_of_suds_of_members_that_do_shifts
    )

    return ShiftAttendanceModeService.annotate_shift_user_data_queryset_with_attendance_mode_at_datetime(
        shift_user_datas, reference_time
    )


class NumberOfPendingResignationsAtDateView(
    LoginRequiredMixin, PermissionRequiredMixin, APIView
):
    permission_required = PERMISSION_COOP_MANAGE

    @extend_schema(
        responses={200: int},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
        ],
    )
    def get(self, request):
        at_date = request.query_params.get("at_date")
        reference_time = datetime.datetime.strptime(at_date, DATE_FORMAT)
        reference_time = timezone.make_aware(reference_time)
        reference_date = reference_time.date()

        return Response(
            MembershipResignation.objects.filter(
                cancellation_date__lte=reference_date, pay_out_day__gte=reference_date
            ).count(),
            status=status.HTTP_200_OK,
        )


class NumberOfCreatedResignationsInSameMonthView(
    LoginRequiredMixin, PermissionRequiredMixin, APIView
):
    permission_required = PERMISSION_COOP_MANAGE

    @extend_schema(
        responses={200: int},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
        ],
    )
    def get(self, request):
        at_date = request.query_params.get("at_date")
        reference_time = datetime.datetime.strptime(at_date, DATE_FORMAT)
        reference_time = timezone.make_aware(reference_time)
        reference_date = reference_time.date()

        return Response(
            MembershipResignation.objects.filter(
                cancellation_date__year=reference_date.year,
                cancellation_date__month=reference_date.month,
            ).count(),
            status=status.HTTP_200_OK,
        )
