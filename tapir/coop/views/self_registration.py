from http import HTTPStatus
from typing import Any

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from tapir.accounts.models import TapirUser
from tapir.coop import config
from tapir.coop.emails.self_registration_confirmation_mail import (
    SelfRegistrationConfirmationMail,
)
from tapir.coop.models import DraftUser, ShareOwner
from tapir.coop.serializers import MemberRegistrationRequestSerializer
from tapir.core.models import FeatureFlag
from tapir.core.services.send_mail_service import SendMailService


class MemberSelfRegistrationTemplateView(TemplateView):
    template_name = "coop/member_self_registration.html"

    @method_decorator(ensure_csrf_cookie)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if not FeatureFlag.get_flag_value(
            config.feature_flag_self_registration_enabled
        ):
            raise PermissionDenied("This feature is currently disabled")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["share_price"] = config.COOP_SHARE_PRICE
        context_data["membership_fee"] = config.COOP_ENTRY_AMOUNT
        context_data["coop_name"] = settings.COOP_NAME
        context_data["coop_street"] = settings.COOP_STREET
        context_data["email_address_member_office"] = (
            settings.EMAIL_ADDRESS_MEMBER_OFFICE
        )

        return context_data


class MemberSelfRegisterApiView(APIView):
    permission_classes = []

    @extend_schema(
        request=MemberRegistrationRequestSerializer,
        responses={200: True, 409: str},
    )
    def post(self, request):
        if not FeatureFlag.get_flag_value(
            config.feature_flag_self_registration_enabled
        ):
            raise PermissionDenied("Self registration is disabled")

        serializer = MemberRegistrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        if (
            TapirUser.objects.filter(email=email).exists()
            or ShareOwner.objects.filter(email=email).exists()
            or DraftUser.objects.filter(email=email).exists()
        ):
            return Response(
                _("This email address ({email}) is already in use".format(email=email)),
                status=HTTPStatus.CONFLICT,
            )

        is_company = serializer.validated_data["is_company"]
        if not is_company:
            delta = relativedelta(
                timezone.now().date(), serializer.validated_data["birthdate"]
            )

            if delta.years < 18:
                return Response(
                    "You must be at least 18 years old",
                    status=HTTPStatus.UNPROCESSABLE_CONTENT,
                )

        with transaction.atomic():
            draft_user = DraftUser.objects.create(
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
                usage_name=serializer.validated_data.get("usage_name"),
                pronouns=serializer.validated_data.get("pronouns"),
                email=serializer.validated_data["email"],
                phone_number=serializer.validated_data.get("phone"),
                birthdate=serializer.validated_data["birthdate"],
                street=serializer.validated_data["street"],
                postcode=serializer.validated_data["postcode"],
                city=serializer.validated_data["city"],
                country=serializer.validated_data["country"],
                num_shares=serializer.validated_data["num_shares"],
                is_investing=serializer.validated_data["is_investing"],
                is_company=is_company,
                company_name=serializer.validated_data.get("company_name", ""),
                preferred_language=serializer.validated_data["preferred_language"],
                ratenzahlung=serializer.validated_data["ratenzahlung"],
            )

            email_builder = SelfRegistrationConfirmationMail(draft_user=draft_user)
            SendMailService.send_to_draft_user(
                actor=None,
                recipient=draft_user,
                email_builder=email_builder,
            )

        return Response(True, status=HTTPStatus.CREATED)
