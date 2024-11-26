import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import generic
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner, MemberStatus
from tapir.settings import PERMISSION_COOP_MANAGE


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
        at_datetime = datetime.datetime.strptime(at_date, "%Y-%d-%m")

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
        at_datetime = datetime.datetime.strptime(at_date, "%Y-%d-%m")

        return Response(
            ShareOwner.objects.with_status(MemberStatus.ACTIVE, at_datetime).count(),
            status=status.HTTP_200_OK,
        )
