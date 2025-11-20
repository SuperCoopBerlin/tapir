from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from tapir.shifts.models import (
    ShiftSlotWarning,
    ShiftSlotWarningTranslation,
    ShiftUserCapabilityTranslation,
    ShiftUserCapability,
    ShiftSlotTemplate,
    ShiftSlot,
)


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


class ShiftUserCapabilityTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftUserCapabilityTranslation
        exclude = ["capability"]


class ShiftUserCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftUserCapability
        fields = ["id", "translations", "shifts"]

    translations = serializers.SerializerMethodField()
    shifts = serializers.SerializerMethodField()

    @extend_schema_field(ShiftUserCapabilityTranslationSerializer(many=True))
    def get_translations(self, capability: ShiftUserCapability):
        return ShiftUserCapabilityTranslationSerializer(
            capability.shiftusercapabilitytranslation_set.all(), many=True
        ).data

    @staticmethod
    def get_shifts(capability: ShiftUserCapability) -> list[str]:
        all_slots: list[ShiftSlotTemplate | ShiftSlot] = list(
            capability.shiftslottemplate_set.prefetch_related("shift_template__group")
        )
        all_slots.extend(
            list(
                capability.shiftslot_set.prefetch_related(
                    "shift__shift_template__group"
                )
            )
        )
        return [slot.get_display_name() for slot in all_slots]


class CreateShiftUserCapabilityRequestSerializer(serializers.Serializer):
    translations = serializers.DictField()  # map language -> name


class UpdateShiftUserCapabilityRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    translations = serializers.DictField()  # map language -> name
