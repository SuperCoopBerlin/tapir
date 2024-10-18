import django_filters
import django_tables2
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
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


class ShareOwnerTableWelcomeDesk(django_tables2.Table):
    class Meta:
        model = ShareOwner
        template_name = TAPIR_TABLE_TEMPLATE
        fields = [
            "id",
        ]
        sequence = (
            "id",
            "display_name",
        )
        order_by = "id"
        attrs = {"class": TAPIR_TABLE_CLASSES}

    display_name = django_tables2.Column(
        empty_values=(), verbose_name="Name", orderable=False
    )

    def before_render(self, request):
        self.request = request

    def render_display_name(self, value, record: ShareOwner):
        display_type = UserUtils.should_viewer_see_short_or_long_display_type(
            self.request.user
        )
        if display_type == UserUtils.DISPLAY_NAME_TYPE_SHORT:
            display_type = UserUtils.DISPLAY_NAME_TYPE_WELCOME_DESK
        return get_html_link(
            reverse("welcomedesk:welcome_desk_share_owner", args=[record.pk]),
            UserUtils.build_display_name(record, display_type),
        )


class ShareOwnerFilterWelcomeDesk(django_filters.FilterSet):
    display_name = CharFilter(
        method="display_name_filter", label=_("Name or member ID")
    )

    @staticmethod
    def display_name_filter(queryset: ShareOwner.ShareOwnerQuerySet, name, value: str):
        if not value:
            return queryset.none()

        if value.isdigit():
            return queryset.filter(id=int(value))

        return queryset.with_name(value)


class WelcomeDeskSearchView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    template_name = "welcomedesk/welcome_desk_search.html"
    table_class = ShareOwnerTableWelcomeDesk
    model = ShareOwner
    filterset_class = ShareOwnerFilterWelcomeDesk

    def get_queryset(self):
        return super().get_queryset().prefetch_related("user")


class WelcomeDeskShareOwnerView(PermissionRequiredMixin, generic.DetailView):
    model = ShareOwner
    template_name = "welcomedesk/welcome_desk_share_owner.html"
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    context_object_name = "share_owner"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)
        share_owner: ShareOwner = context_data["share_owner"]

        context_data["can_shop"] = share_owner.can_shop()

        context_data["missing_account"] = share_owner.user is None
        if context_data["missing_account"]:
            return context_data

        context_data["is_frozen"] = (
            share_owner.user.shift_user_data.attendance_mode
            == ShiftAttendanceMode.FROZEN
        )

        context_data["must_register_to_a_shift"] = (
            share_owner.user.shift_user_data.attendance_mode
            == ShiftAttendanceMode.REGULAR
            and not ShiftAttendanceTemplate.objects.filter(
                user=share_owner.user
            ).exists()
            and not share_owner.user.shift_user_data.is_currently_exempted_from_shifts()
        )

        context_data["is_paused"] = (
            MembershipPause.objects.filter(share_owner=share_owner)
            .active_temporal()
            .exists()
        )

        return context_data


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
