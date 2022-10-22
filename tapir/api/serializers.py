from rest_framework import serializers

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import (
    Shift,
    ShiftUserData,
    ShiftAttendance,
    SHIFT_USER_CAPABILITY_CHOICES,
)


class ShiftAttendanceSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    slot_name = serializers.CharField(source="slot.name", read_only=True)

    class Meta:
        model = ShiftAttendance
        fields = "__all__"


class ShiftSerializer(serializers.ModelSerializer):
    absolute_url = serializers.CharField(source="get_absolute_url", read_only=True)
    attendances = ShiftAttendanceSerializer(
        source="get_attendances", read_only=True, many=True
    )

    class Meta:
        model = Shift
        fields = "__all__"


class ShareOwnerSerializer(serializers.ModelSerializer):
    can_shop = serializers.BooleanField(read_only=True)
    num_shares = serializers.IntegerField(read_only=True)
    status = serializers.CharField(source="get_member_status", read_only=True)
    absolute_url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = ShareOwner
        fields = "__all__"


class StringListField(serializers.ListField):
    child = serializers.CharField()


class ShiftUserDataSerializer(serializers.ModelSerializer):
    capabilities = StringListField()
    known_capabilities = serializers.SerializerMethodField()

    class Meta:
        model = ShiftUserData
        fields = ["capabilities", "known_capabilities"]

    @staticmethod
    def get_known_capabilities(obj):
        return SHIFT_USER_CAPABILITY_CHOICES.keys()


class TapirUserSerializer(serializers.ModelSerializer):
    share_owner = ShareOwnerSerializer(many=False, read_only=True)
    shift_user_data = ShiftUserDataSerializer(many=False, read_only=True)

    class Meta:
        model = TapirUser
        exclude = ["password"]
        depth = 1
