import django_filters
import django_tables2
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic import TemplateView
from django_filters import CharFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner, MembershipPause
from tapir.coop.services.InvestingStatusService import InvestingStatusService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.coop.services.NumberOfSharesService import NumberOfSharesService
from tapir.core.config import TAPIR_TABLE_TEMPLATE, TAPIR_TABLE_CLASSES
from tapir.settings import PERMISSION_WELCOMEDESK_VIEW
from tapir.shifts.models import ShiftAttendanceMode, ShiftAttendanceTemplate
from tapir.shifts.services.shift_attendance_mode_service import (
    ShiftAttendanceModeService,
)
from tapir.utils.shortcuts import get_html_link
from tapir.utils.user_utils import UserUtils
from tapir.welcomedesk.serializers import ShareOwnerForWelcomeDeskSerializer


class WelcomeDeskSearchView(PermissionRequiredMixin, TemplateView):
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    template_name = "welcomedesk/welcome_desk_search.html"


class SearchMemberForWelcomeDeskView(APIView):
    @extend_schema(
        responses={200: ShareOwnerForWelcomeDeskSerializer(many=True)},
        parameters=[
            OpenApiParameter(name="search_input", required=True, type=str),
        ],
    )
    def get(self, request):
        search_input = request.query_params.get("search_input")

        reference_time = timezone.now()
        reference_date = reference_time.date()

        share_owners = self.get_share_owners(search_input)
        share_owners = self.optimize_queryset_for_faster_loading_time(
            share_owners, reference_time, reference_date
        )

        serializer = ShareOwnerForWelcomeDeskSerializer(
            share_owners,
            many=True,
            read_only=True,
            context={
                "request": request,
                "reference_time": reference_time,
                "reference_date": reference_date,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def optimize_queryset_for_faster_loading_time(
        queryset, reference_time, reference_date
    ):
        queryset = queryset.prefetch_related("user", "user__shift_user_data")

        queryset = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
            queryset, reference_date
        )
        queryset = (
            MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                queryset, reference_date
            )
        )
        queryset = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
            queryset, reference_time
        )
        queryset = ShiftAttendanceModeService.annotate_share_owner_queryset_with_attendance_mode_at_date(
            queryset, reference_date
        )

        return queryset

    @staticmethod
    def get_share_owners(search_input: str):
        queryset = ShareOwner.objects.all()

        if not search_input:
            return queryset.none()

        if search_input.isdigit():
            return queryset.filter(id=int(search_input))

        return queryset.with_name(search_input)
