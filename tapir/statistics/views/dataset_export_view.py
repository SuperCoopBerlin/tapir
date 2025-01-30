import datetime
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner
from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.serializers import DatapointExportSerializer
from tapir.statistics.services.data_providers.base_data_provider import data_providers
from tapir.statistics.services.datapoint_export_column_builder import (
    DatapointExportColumnBuilder,
)


class DatasetExportView(LoginRequiredMixin, PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_COOP_MANAGE

    @extend_schema(
        responses={200: DatapointExportSerializer(many=True)},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
            OpenApiParameter(name="export_columns", required=True, type=str, many=True),
            OpenApiParameter(name="dataset", required=True, type=str),
        ],
    )
    def get(self, request):
        reference_time = self.get_reference_time(request)
        export_columns = request.query_params.getlist("export_columns")

        queryset = data_providers[request.query_params.get("dataset")].get_queryset(
            reference_time
        )

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

    @staticmethod
    def get_reference_time(request):
        at_date = request.query_params.get("at_date")
        reference_time = datetime.datetime.strptime(at_date, "%Y-%m-%d")
        return timezone.make_aware(reference_time)
