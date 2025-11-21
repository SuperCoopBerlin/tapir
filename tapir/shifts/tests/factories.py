import datetime
import math

import factory

from tapir.shifts.models import (
    ShiftTemplate,
    WEEKDAY_CHOICES,
    ShiftSlotTemplate,
    Shift,
    ShiftSlot,
    ShiftUserCapabilityTranslation,
    ShiftUserCapability,
    ShiftSlotWarning,
    ShiftSlotWarningTranslation,
)


class ShiftSlotTemplateFactory(factory.django.DjangoModelFactory[ShiftSlotTemplate]):
    class Meta:
        model = ShiftSlotTemplate

    name = factory.Faker("job")


class ShiftTemplateFactory(factory.django.DjangoModelFactory[ShiftTemplate]):
    class Meta:
        model = ShiftTemplate
        exclude = ("start_hour", "start_minute", "duration")

    name = factory.Faker("bs")
    weekday = factory.Iterator(WEEKDAY_CHOICES, getter=lambda day_choice: day_choice[0])

    start_hour = factory.Faker("pyint", max_value=19)
    start_minute = factory.Faker("pyint", max_value=59)
    duration = factory.Faker("pyint", min_value=1, max_value=4)
    start_time = factory.LazyAttribute(
        lambda shift_template: datetime.time(
            hour=shift_template.start_hour,
            minute=shift_template.start_minute,
        )
    )
    end_time = factory.LazyAttribute(
        lambda shift_template: datetime.time(
            hour=shift_template.start_hour + shift_template.duration,
            minute=shift_template.start_minute,
        )
    )

    @factory.post_generation
    def nb_slots(self, create, nb_slots, **kwargs):
        if not create:
            return
        if nb_slots is None:
            nb_slots = 1
        for _ in range(nb_slots):
            ShiftSlotTemplateFactory.create(shift_template=self)
        if not self.num_required_attendances:
            self.num_required_attendances = math.ceil(nb_slots / 2)
        self.save()


class ShiftSlotFactory(factory.django.DjangoModelFactory[ShiftSlot]):
    class Meta:
        model = ShiftSlot

    name = factory.Faker("job")


class ShiftFactory(factory.django.DjangoModelFactory[Shift]):
    class Meta:
        model = Shift
        exclude = ("start_hour", "start_minute", "duration", "nb_slots")
        skip_postgeneration_save = True

    name = factory.Faker("bs")

    duration = factory.Faker("pyint", min_value=1, max_value=4)
    start_time = factory.Faker("date_time", tzinfo=datetime.UTC)
    end_time = factory.LazyAttribute(
        lambda shift_template: shift_template.start_time
        + datetime.timedelta(hours=shift_template.duration)
    )

    @factory.post_generation
    def nb_slots(self, create, nb_slots, **kwargs):
        if not create:
            return
        if nb_slots is None:
            nb_slots = 1
        for _ in range(nb_slots):
            ShiftSlotFactory.create(shift=self)
        self.num_required_attendances = math.ceil(nb_slots / 2)
        self.save()


class ShiftSlotWarningTranslationFactory(
    factory.django.DjangoModelFactory[ShiftSlotWarningTranslation]
):
    class Meta:
        model = ShiftSlotWarningTranslation

    name = factory.Faker("sentence")
    description = factory.Faker("bs")


class ShiftSlotWarningFactory(factory.django.DjangoModelFactory[ShiftSlotWarning]):
    class Meta:
        model = ShiftSlotWarning

    @factory.post_generation
    def translations(self: ShiftSlotWarning, create, languages, **kwargs):
        if not create:
            return
        if languages is None:
            languages = ["en"]
        for language in languages:
            ShiftSlotWarningTranslationFactory.create(warning=self, language=language)
        self.save()


class ShiftUserCapabilityTranslationFactory(
    factory.django.DjangoModelFactory[ShiftUserCapabilityTranslation]
):
    class Meta:
        model = ShiftUserCapabilityTranslation

    name = factory.Faker("sentence")
    description = factory.Faker("bs")


class ShiftUserCapabilityFactory(
    factory.django.DjangoModelFactory[ShiftUserCapability]
):
    class Meta:
        model = ShiftUserCapability

    @factory.post_generation
    def translations(self: ShiftUserCapability, create, languages, **kwargs):
        if not create:
            return
        if languages is None:
            languages = ["en"]
        for language in languages:
            ShiftUserCapabilityTranslationFactory.create(
                capability=self, language=language
            )
        self.save()
