from distinctipy import distinctipy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from drf_spectacular.utils import extend_schema
from icecream import ic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.serializers import DatasetSerializer
from tapir.statistics.services.data_providers import *  # noqa
from tapir.statistics.services.data_providers.base_data_provider import data_providers


class AvailableDatasetsView(LoginRequiredMixin, PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_COOP_MANAGE
    POINT_STYLES = [
        "circle",
        "cross",
        "crossRot",
        "dash",
        "line",
        "rect",
        "rectRounded",
        "rectRot",
        "star",
        "triangle",
    ]

    @extend_schema(
        responses={200: DatasetSerializer(many=True)},
    )
    def get(self, request):
        datasets = [
            {
                "id": provider_id,
                "display_name": provider.get_display_name(),
                "description": provider.get_description(),
            }
            for provider_id, provider in data_providers.items()
        ]
        ic(data_providers.items())

        colors = distinctipy.get_colors(len(datasets))
        for index, dataset in enumerate(datasets):
            dataset["color"] = colors[index]
            dataset["point_style"] = self.POINT_STYLES[index % len(self.POINT_STYLES)]

        return Response(
            DatasetSerializer(datasets, many=True).data,
            status=status.HTTP_200_OK,
        )
