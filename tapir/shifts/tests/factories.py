import datetime
import math

import factory

from tapir.shifts.models import ShiftTemplate, WEEKDAY_CHOICES, ShiftSlotTemplate


class ShiftSlotTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShiftSlotTemplate

    name = factory.Faker("job")


class ShiftTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShiftTemplate
        exclude = ("start_hour", "start_minute", "duration", "nb_slots")

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
        nb_slots = nb_slots or 1
        for _ in range(nb_slots):
            ShiftSlotTemplateFactory.create(shift_template=self)
        self.num_required_attendances = math.ceil(nb_slots / 2)
        self.save()
