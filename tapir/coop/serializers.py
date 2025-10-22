from rest_framework import serializers

from tapir.accounts.models import TapirUser


class TapirUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TapirUser
        fields = "__all__"

    country = serializers.CharField()


class MemberRegistrationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    number_of_coop_shares = serializers.IntegerField()
