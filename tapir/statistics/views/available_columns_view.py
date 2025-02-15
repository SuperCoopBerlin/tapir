from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.serializers import ColumnSerializer, DatapointExportSerializer


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
