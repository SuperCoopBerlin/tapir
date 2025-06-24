from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from tapir.shifts.models import ShiftSlotWarning, ShiftSlotWarningTranslation


class ShiftSlotWarningTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSlotWarningTranslation
        exclude = ["warning"]


class ShiftSlotWarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSlotWarning
        fields = ["id", "translations", "shifts"]

    translations = serializers.SerializerMethodField()
    shifts = serializers.SerializerMethodField()

    @extend_schema_field(ShiftSlotWarningTranslationSerializer(many=True))
    def get_translations(self, warning: ShiftSlotWarning):
        return ShiftSlotWarningTranslationSerializer(
            warning.shiftslotwarningtranslation_set.all(), many=True
        ).data

    @staticmethod
    def get_shifts(warning: ShiftSlotWarning) -> list[str]:
        all_slots = list(warning.shiftslottemplate_set.all())
        all_slots.extend(list(warning.shiftslot_set.all()))
        return [slot.get_display_name() for slot in all_slots]


class CreateShiftSlotWarningRequestSerializer(serializers.Serializer):
    translations = serializers.DictField()  # map language -> name


class UpdateShiftSlotWarningRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    translations = serializers.DictField()  # map language -> name


class LanguageSerializer(serializers.Serializer):
    short_name = serializers.CharField()
    display_name = serializers.CharField()
