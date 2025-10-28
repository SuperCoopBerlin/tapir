from rest_framework import serializers

from tapir.accounts.models import TapirUser
from tapir.utils.models import COUNTRIES, PREFERRED_LANGUAGES


class TapirUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TapirUser
        fields = "__all__"

    country = serializers.CharField()


class MemberRegistrationRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_company = serializers.BooleanField()
    is_investing = serializers.BooleanField()
    num_shares = serializers.IntegerField()

    company_name = serializers.CharField(required=False)
    usage_name = serializers.CharField(required=False, allow_blank=True)
    pronouns = serializers.CharField(required=False, allow_blank=True)
    birthdate = serializers.DateField()
    preferred_language = serializers.ChoiceField(required=True, choices=PREFERRED_LANGUAGES)

    street = serializers.CharField()
    city = serializers.CharField()
    postcode = serializers.CharField()
    country = serializers.ChoiceField(choices=COUNTRIES)

    email = serializers.EmailField()
    phone = serializers.CharField(required=False)

    other_comments = serializers.CharField(required=False)
