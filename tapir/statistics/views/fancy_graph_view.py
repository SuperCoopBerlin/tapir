import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.views import generic
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.accounts.models import TapirUser
from tapir.accounts.services.co_purchaser_history_service import (
    CoPurchaserHistoryService,
)
from tapir.coop.models import ShareOwner, MemberStatus
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import (
    ShiftUserData,
    UpdateShiftUserDataLogEntry,
    ShiftAttendanceMode,
)
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService
from tapir.shifts.services.shift_partner_history_service import (
    ShiftPartnerHistoryService,
)

DATE_FORMAT = "%Y-%m-%d"


class FancyGraphView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    permission_required = PERMISSION_COOP_MANAGE
    template_name = "statistics/fancy_graph.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data


class NumberOfMembersAtDateView(LoginRequiredMixin, PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_COOP_MANAGE

    @extend_schema(
        responses={200: int},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
        ],
    )
    def get(self, request):
        at_date = request.query_params.get("at_date")
        at_datetime = datetime.datetime.strptime(at_date, DATE_FORMAT)

        total_count = 0
        for member_status in [
            MemberStatus.ACTIVE,
            MemberStatus.PAUSED,
            MemberStatus.INVESTING,
        ]:
            total_count += ShareOwner.objects.with_status(
                member_status, at_datetime
            ).count()

        return Response(
            total_count,
            status=status.HTTP_200_OK,
        )


class NumberOfActiveMembersAtDateView(
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
        at_datetime = datetime.datetime.strptime(at_date, DATE_FORMAT)

        return Response(
            ShareOwner.objects.with_status(MemberStatus.ACTIVE, at_datetime).count(),
            status=status.HTTP_200_OK,
        )


class NumberOfWorkingMembersAtDateView(
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
        reference_time = timezone.make_aware(
            datetime.datetime.strptime(at_date, DATE_FORMAT)
        )
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
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            ShareOwner.objects.all(), reference_date
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
            self.transfer_attributes(
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

        count = len(
            [
                shift_user_data
                for shift_user_data in shift_user_datas
                if ShiftExpectationService.is_member_expected_to_do_shifts(
                    shift_user_data, reference_time
                )
            ]
        )

        return Response(
            count,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def transfer_attributes(source, target, attributes):
        for attribute in attributes:
            setattr(target, attribute, getattr(source, attribute))


class NumberOfPurchasingMembersAtDateView(
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

        purchasing_members = self.get_purchasing_members_at_date(reference_time)

        return Response(
            len(purchasing_members),
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def get_purchasing_members_at_date(reference_time):
        reference_date = reference_time.date()

        share_owners = (
            ShareOwner.objects.all()
            .prefetch_related("user")
            .prefetch_related("user__shift_user_data")
            .prefetch_related("share_ownerships")
        )
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            share_owners, reference_date
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, reference_date
            )
        )
        share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            share_owners, reference_time
        )
        share_owners = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_time
        )

        return [
            share_owner
            for share_owner in share_owners
            if share_owner.can_shop(reference_time)
        ]


class NumberOfFrozenMembersAtDateView(
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

        share_owners = self.get_members_frozen_at_datetime(reference_time)

        count = share_owners.count()

        return Response(
            count,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def get_members_frozen_at_datetime(reference_time):
        reference_date = reference_time.date()
        share_owners = (
            ShareOwner.objects.all()
            .prefetch_related("user")
            .prefetch_related("user__shift_user_data")
            .prefetch_related("share_ownerships")
        )
        share_owners = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            share_owners, reference_date
        )
        share_owners = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                share_owners, reference_date
            )
        )
        share_owners = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            share_owners, reference_time
        )
        share_owners = share_owners.with_status(MemberStatus.ACTIVE)

        share_owners = FrozenStatusHistoryService.annotate_share_owner_queryset_with_is_frozen_at_datetime(
            share_owners, reference_time
        )

        return share_owners.filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: True}
        )


class NumberOfLongTermFrozenMembersAtDateView(
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

        share_owners = NumberOfFrozenMembersAtDateView.get_members_frozen_at_datetime(
            reference_time
        ).prefetch_related("user")

        count = 0
        for share_owner in share_owners:
            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user=share_owner.user,
                    created_date__lte=reference_time,
                    new_values__is_frozen="True",
                )
                .order_by("-created_date")
                .first()
            )

            if status_change_log_entry:
                if (
                    reference_time - status_change_log_entry.created_date
                ).days > 30 * 6:
                    count += 1
                continue

            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user=share_owner.user,
                    created_date__lte=reference_time,
                    new_values__attendance_mode=ShiftAttendanceMode.FROZEN,
                )
                .order_by("-created_date")
                .first()
            )

            if status_change_log_entry:
                if (
                    reference_time - status_change_log_entry.created_date
                ).days > 30 * 6:
                    count += 1
                continue

            # could not find any log entry, we assume the member is frozen long-term
            count += 1

        return Response(
            count,
            status=status.HTTP_200_OK,
        )


class NumberOfShiftPartnersAtDateView(
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

        active_members = ShareOwner.objects.with_status(
            MemberStatus.ACTIVE, reference_time
        )
        shift_user_datas = ShiftUserData.objects.filter(
            user__share_owner__in=active_members
        )

        shift_user_datas = ShiftPartnerHistoryService.annotate_shift_user_data_queryset_with_has_shift_partner_at_date(
            shift_user_datas, reference_time
        )
        shift_user_datas = shift_user_datas.filter(
            **{ShiftPartnerHistoryService.ANNOTATION_HAS_SHIFT_PARTNER: True}
        )

        return Response(
            shift_user_datas.count(),
            status=status.HTTP_200_OK,
        )


class NumberOfCoPurchasersAtDateView(
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

        tapir_users = TapirUser.objects.all()
        purchasing_members = (
            NumberOfPurchasingMembersAtDateView.get_purchasing_members_at_date(
                reference_time
            )
        )
        tapir_users = tapir_users.filter(share_owner__in=purchasing_members)

        tapir_users = CoPurchaserHistoryService.annotate_tapir_user_queryset_with_has_co_purchaser_at_date(
            tapir_users, reference_time
        )
        tapir_users = tapir_users.filter(
            **{CoPurchaserHistoryService.ANNOTATION_HAS_CO_PURCHASER: True}
        )

        return Response(
            tapir_users.count(),
            status=status.HTTP_200_OK,
        )


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


class NumberOfFlyingMembersAtDateView(
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

        shift_user_datas = (
            get_shift_user_datas_of_working_members_annotated_with_attendance_mode(
                reference_time
            )
        )

        shift_user_datas = shift_user_datas.filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.FLYING
            }
        )

        return Response(
            shift_user_datas.count(),
            status=status.HTTP_200_OK,
        )


class NumberOfAbcdMembersAtDateView(
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

        shift_user_datas = (
            get_shift_user_datas_of_working_members_annotated_with_attendance_mode(
                reference_time
            )
        )

        shift_user_datas = shift_user_datas.filter(
            **{
                ShiftAttendanceModeService.ANNOTATION_SHIFT_ATTENDANCE_MODE_AT_DATE: ShiftAttendanceMode.REGULAR
            }
        )

        return Response(
            shift_user_datas.count(),
            status=status.HTTP_200_OK,
        )
