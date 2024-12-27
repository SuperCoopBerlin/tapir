import datetime
from abc import ABC, abstractmethod

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.views import generic
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.settings import PERMISSION_COOP_MANAGE
from tapir.statistics.models import FancyGraphCache


class FancyGraphView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    permission_required = PERMISSION_COOP_MANAGE
    template_name = "statistics/fancy_graph.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data


class DatapointView(LoginRequiredMixin, PermissionRequiredMixin, APIView, ABC):
    permission_required = PERMISSION_COOP_MANAGE

    @abstractmethod
    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        pass

    def get_datapoint(self, reference_time: datetime.datetime):
        reference_date = reference_time.date()
        view_name = f"{self.__class__.__module__}.{self.__class__.__name__}"

        if reference_date < timezone.now().date():
            # Only use the cache for dates in the past:
            # someone may make changes and check the results on the graph on the same day.
            cached_value = FancyGraphCache.objects.filter(
                view_name=view_name, date=reference_date
            ).first()
            if cached_value:
                return cached_value.value

        value = self.calculate_datapoint(reference_time)
        FancyGraphCache.objects.create(
            view_name=view_name, date=reference_date, value=value
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
        ],
    )
    def get(self, request):
        reference_time = self.get_reference_time(request)
        relative = request.query_params.get("relative") == "true"

        result = self.get_datapoint(reference_time)

        if relative:
            previous_datapoint_time = (
                reference_time - datetime.timedelta(days=1)
            ).replace(day=1)
            previous_datapoint = self.get_datapoint(previous_datapoint_time)
            result = result - previous_datapoint

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
