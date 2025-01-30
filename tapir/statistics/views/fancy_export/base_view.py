import datetime
from abc import ABC
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import generic
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.serializers import DatapointExportSerializer, ColumnSerializer
from tapir.statistics.services.datapoint_export_column_builder import (
    DatapointExportColumnBuilder,
)
from tapir.statistics.views.fancy_graph.base_view import DatapointView


class FancyExportView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    permission_required = PERMISSION_COOP_MANAGE
    template_name = "statistics/fancy_export.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data


class DatapointExportView(DatapointView, ABC):
    @extend_schema(
        responses={200: DatapointExportSerializer(many=True)},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
            OpenApiParameter(name="export_columns", required=True, type=str, many=True),
        ],
    )
    def get(self, request):
        reference_time = self.get_reference_time(request)
        export_columns = request.query_params.getlist("export_columns")

        queryset = self.get_queryset(reference_time).distinct().order_by("id")

        return Response(
            DatapointExportSerializer(
                self.build_serializer_data(queryset, export_columns, reference_time),
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def build_serializer_data(
        self, queryset, export_columns: List[str], reference_time: datetime.datetime
    ):
        return [
            self.build_single_entry_data(share_owner, export_columns, reference_time)
            for share_owner in queryset
        ]

    def build_single_entry_data(
        self,
        share_owner: ShareOwner,
        export_columns: List[str],
        reference_time: datetime.datetime,
    ):
        return {
            column_name: self.build_column_data(
                share_owner, column_name, reference_time
            )
            for column_name in export_columns
        }

    @staticmethod
    def build_column_data(
        share_owner: ShareOwner, column_name: str, reference_time: datetime.datetime
    ):
        function_name = f"build_column_{column_name}"
        return getattr(DatapointExportColumnBuilder, function_name)(
            share_owner=share_owner, reference_time=reference_time
        )


class AvailableColumnsView(LoginRequiredMixin, PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_COOP_MANAGE

    @extend_schema(
        responses={200: ColumnSerializer(many=True)},
    )
    def get(self, request):
        objects = [
            {"column_name": column_name}
            for column_name in DatapointExportSerializer().get_fields().keys()
        ]

        return Response(
            ColumnSerializer(objects, many=True).data,
            status=status.HTTP_200_OK,
        )
