from rest_framework import serializers

from tapir.accounts.models import TapirUser


class TapirUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TapirUser
        fields = "__all__"

    country = serializers.CharField()
