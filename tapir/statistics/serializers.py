from rest_framework import serializers


class DatasetSerializer(serializers.Serializer):
    id = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField()
    color = serializers.CharField()
    point_style = serializers.CharField()


class DatapointExportSerializer(serializers.Serializer):
    member_number = serializers.IntegerField(required=False)
    display_name = serializers.CharField(required=False)
    is_company = serializers.BooleanField(required=False)
    company_name = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    usage_name = serializers.CharField(required=False)
    pronouns = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    birthdate = serializers.CharField(required=False)
    street = serializers.CharField(required=False)
    street_2 = serializers.CharField(required=False)
    postcode = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    preferred_language = serializers.CharField(required=False)
    is_investing = serializers.BooleanField(required=False)
    ratenzahlung = serializers.BooleanField(required=False)
    attended_welcome_session = serializers.BooleanField(required=False)
    co_purchaser = serializers.CharField(required=False)
    allows_purchase_tracking = serializers.BooleanField(required=False)
    shift_capabilities = serializers.ListField(
        required=False, child=serializers.CharField()
    )
    shift_partner = serializers.IntegerField(required=False)
    shift_status = serializers.CharField(required=False)
    is_working = serializers.BooleanField(required=False)
    is_exempted = serializers.BooleanField(required=False)
    is_paused = serializers.BooleanField(required=False)
    can_shop = serializers.BooleanField(required=False)


class ColumnSerializer(serializers.Serializer):
    column_name = serializers.CharField()
