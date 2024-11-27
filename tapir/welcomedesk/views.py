from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.coop.models import ShareOwner
from tapir.coop.services.NumberOfSharesService import NumberOfSharesService
from tapir.settings import PERMISSION_WELCOMEDESK_VIEW
from tapir.welcomedesk.serializers import ShareOwnerForWelcomeDeskSerializer
from tapir.welcomedesk.services.welcome_desk_reasons_cannot_shop_service import (
    WelcomeDeskReasonsCannotShopService,
)
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


class WelcomeDeskSearchView(PermissionRequiredMixin, TemplateView):
    permission_required = PERMISSION_WELCOMEDESK_VIEW
    template_name = "welcomedesk/welcome_desk_search.html"


class SearchMemberForWelcomeDeskView(PermissionRequiredMixin, APIView):
    permission_required = PERMISSION_WELCOMEDESK_VIEW

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

        # Trying to run the annotations on a smaller queryset
        ids = [share_owner.id for share_owner in share_owners]
        share_owners = ShareOwner.objects.filter(id__in=ids)

        share_owners = self.optimize_queryset(
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
    def optimize_queryset(queryset, reference_time, reference_date):
        queryset = WelcomeDeskWarningsService.optimize_queryset_for_this_service(
            queryset, reference_time
        )
        queryset = (
            WelcomeDeskReasonsCannotShopService.optimize_queryset_for_this_service(
                queryset, reference_time=reference_time, reference_date=reference_date
            )
        )
        queryset = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
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
