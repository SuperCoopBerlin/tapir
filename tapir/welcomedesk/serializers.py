import datetime

from django.core.handlers.wsgi import WSGIRequest
from rest_framework import serializers

from tapir.coop.models import ShareOwner
from tapir.coop.services.member_can_shop_service import MemberCanShopService
from tapir.utils.user_utils import UserUtils
from tapir.welcomedesk.services.welcome_desk_reasons_cannot_shop_service import (
    WelcomeDeskReasonsCannotShopService,
)
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


def split_name(full_name):
    "Currently, only full-names are stored for co-purchaser. This could be replaced by a new Co-Purchaser-model storing first and last name separately and make this function obsolete (here)"
    if not full_name:
        return "", ""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    i_split = -1

    prefixes = {"von", "van", "de", "der", "den", "del", "da", "du", "le", "la"}
    if any(part.lower() in prefixes for part in parts):
        for i, part in enumerate(parts):
            if part.lower() in prefixes:
                i_split = i
                break

    return " ".join(parts[:i_split]), " ".join(parts[i_split:])


class ShareOwnerForWelcomeDeskSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    can_shop = serializers.SerializerMethodField()
    co_purchaser = serializers.SerializerMethodField()
    co_purchaser_2 = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField()
    reasons_cannot_shop = serializers.SerializerMethodField()

    class Meta:
        model = ShareOwner
        fields = [
            "id",
            "display_name",
            "can_shop",
            "co_purchaser",
            "co_purchaser_2",
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
        return MemberCanShopService.can_shop(share_owner, self.reference_time)

    @staticmethod
    def get_co_purchaser(share_owner: ShareOwner) -> str | None:
        if not share_owner.user:
            return None
        first_name, last_name = split_name(share_owner.user.co_purchaser)
        if not last_name:
            return first_name

        initials = ".".join(word[0] for word in last_name.split()) + "."
        return f"{first_name} {initials}".strip()

    @staticmethod
    def get_co_purchaser_2(share_owner: ShareOwner) -> str | None:
        if not share_owner.user:
            return None
        first_name, last_name = split_name(share_owner.user.co_purchaser_2)
        if not last_name:
            return first_name

        initials = ".".join(word[0] for word in last_name.split()) + "."
        return f"{first_name} {initials}".strip()

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
