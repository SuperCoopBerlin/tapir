import datetime
from abc import ABC
from typing import Type

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.models import FancyGraphCache
from tapir.statistics.services.data_providers.base_data_provider import (
    data_providers,
    BaseDataProvider,
)


class DatasetGraphPointView(LoginRequiredMixin, PermissionRequiredMixin, APIView, ABC):
    permission_required = PERMISSION_COOP_MANAGE

    @staticmethod
    def calculate_datapoint(
        data_provider: Type[BaseDataProvider], reference_time: datetime.datetime
    ) -> int:
        return data_provider.get_queryset(reference_time).distinct().count()

    def get_datapoint(
        self, data_provider: Type[BaseDataProvider], reference_time: datetime.datetime
    ):
        reference_date = reference_time.date()
        data_provider_name = (
            f"{data_provider.__class__.__module__}.{data_provider.__class__.__name__}"
        )

        if reference_date < timezone.now().date():
            # Only use the cache for dates in the past:
            # someone may make changes and check the results on the graph on the same day.
            cached_value = FancyGraphCache.objects.filter(
                data_provider_name=data_provider_name, date=reference_date
            ).first()
            if cached_value:
                return cached_value.value

        value = self.calculate_datapoint(data_provider, reference_time)
        FancyGraphCache.objects.create(
            data_provider_name=data_provider_name, date=reference_date, value=value
        )
        return value

    @staticmethod
    def get_reference_time(request):
        at_date = request.query_params.get("at_date")
        reference_time = datetime.datetime.strptime(at_date, "%Y-%m-%d")
        return timezone.make_aware(reference_time)

    @staticmethod
    def transfer_attributes(source, target, attributes):
        for attribute in attributes:
            setattr(target, attribute, getattr(source, attribute))

    @extend_schema(
        responses={200: int},
        parameters=[
            OpenApiParameter(name="at_date", required=True, type=datetime.date),
            OpenApiParameter(name="relative", required=True, type=bool),
            OpenApiParameter(name="dataset", required=True, type=str),
        ],
    )
    def get(self, request):
        reference_time = self.get_reference_time(request)
        relative = request.query_params.get("relative") == "true"

        data_provider = data_providers[request.query_params.get("dataset")]

        result = self.get_datapoint(data_provider, reference_time)

        if relative:
            previous_datapoint_time = (
                reference_time - datetime.timedelta(days=1)
            ).replace(day=1)
            previous_datapoint = self.get_datapoint(
                data_provider, previous_datapoint_time
            )
            result = result - previous_datapoint

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
