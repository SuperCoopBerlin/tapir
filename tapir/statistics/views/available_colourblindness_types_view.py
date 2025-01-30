from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.settings import PERMISSION_COOP_MANAGE


class AvailableColourblindnessTypes(
    LoginRequiredMixin, PermissionRequiredMixin, APIView
):
    permission_required = PERMISSION_COOP_MANAGE

    # From https://distinctipy.readthedocs.io/en/latest/api.html#module-distinctipy.colorblind
    COLOURBLINDNESS_TYPES = [
        "Protanopia",
        "Protanomaly",
        "Deuteranopia",
        "Deuteranomaly",
        "Tritanopia",
        "Tritanomaly",
        "Achromatopsia",
        "Achromatomaly",
    ]

    @extend_schema(
        responses={200: List[str]},
    )
    def get(self, request):
        return Response(
            self.COLOURBLINDNESS_TYPES,
            status=status.HTTP_200_OK,
        )
