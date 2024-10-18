import datetime

from django.core.handlers.wsgi import WSGIRequest
from rest_framework import serializers

from tapir.coop.models import ShareOwner
from tapir.utils.user_utils import UserUtils


class ShareOwnerForWelcomeDeskSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    can_shop = serializers.SerializerMethodField()

    class Meta:
        model = ShareOwner
        fields = ["id", "display_name", "can_shop"]

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
