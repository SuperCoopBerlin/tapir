import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.views import generic
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.coop.services.investing_status_service import InvestingStatusService
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.coop.services.number_of_shares_service import NumberOfSharesService
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.shifts.models import ShiftUserData
from tapir.shifts.services.frozen_status_history_service import (
    FrozenStatusHistoryService,
)
from tapir.shifts.services.shift_expectation_service import ShiftExpectationService

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

        count = len(
            [
                share_owner
                for share_owner in share_owners
                if share_owner.can_shop(reference_time)
            ]
        )

        return Response(
            count,
            status=status.HTTP_200_OK,
        )


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

        count = share_owners.filter(
            **{FrozenStatusHistoryService.ANNOTATION_IS_FROZEN_AT_DATE: True}
        ).count()

        return Response(
            count,
            status=status.HTTP_200_OK,
        )
