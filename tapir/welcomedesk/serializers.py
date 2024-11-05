import datetime

from django.core.handlers.wsgi import WSGIRequest
from rest_framework import serializers

from tapir.coop.models import ShareOwner
from tapir.utils.user_utils import UserUtils
from tapir.welcomedesk.services.welcome_desk_reasons_cannot_shop_service import (
    WelcomeDeskReasonsCannotShopService,
)
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


class ShareOwnerForWelcomeDeskSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    can_shop = serializers.SerializerMethodField()
    co_purchaser = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField()
    reasons_cannot_shop = serializers.SerializerMethodField()

    class Meta:
        model = ShareOwner
        fields = [
            "id",
            "display_name",
            "can_shop",
            "co_purchaser",
            "warnings",
            "reasons_cannot_shop",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request: WSGIRequest = self.context.get("request")
        self.reference_time: datetime.datetime = self.context.get("reference_time")
        self.reference_date: datetime.date = self.context.get("reference_date")

    def get_display_name(self, share_owner: ShareOwner) -> str:
        display_type = UserUtils.should_viewer_see_short_or_long_display_type(
            self.request.user
        )
        if display_type == UserUtils.DISPLAY_NAME_TYPE_SHORT:
            display_type = UserUtils.DISPLAY_NAME_TYPE_WELCOME_DESK
        return UserUtils.build_display_name(share_owner, display_type)

    def get_can_shop(self, share_owner: ShareOwner) -> bool:
        return share_owner.can_shop(self.reference_time)

    @staticmethod
    def get_co_purchaser(share_owner: ShareOwner) -> str | None:
        if not share_owner.user:
            return None
        return share_owner.user.co_purchaser

    def get_warnings(self, share_owner: ShareOwner) -> list[str]:
        return WelcomeDeskWarningsService.build_warnings(
            share_owner=share_owner, request_user=self.request.user
        )

    def get_reasons_cannot_shop(self, share_owner: ShareOwner) -> list[str]:
        return WelcomeDeskReasonsCannotShopService.build_reasons_why_this_member_cannot_shop(
            share_owner=share_owner,
            request_user=self.request.user,
            reference_time=self.reference_time,
            reference_date=self.reference_date,
        )
