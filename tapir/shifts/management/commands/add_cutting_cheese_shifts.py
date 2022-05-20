import datetime

from django.core.management.base import BaseCommand
from tapir.shifts.models import ShiftTemplate, ShiftSlotTemplate


#
# for testing start this command with
#  docker compose exec web poetry run python manage.py add_cutting_cheese_shifts
#
class Command(BaseCommand):
    help = "New shift 'Kaesetheke' needed as described in internal dict NEWSHIFTSLOTS"
    MONDAY = 0
    WEDNESDAY = 2
    SATURDAY = 5

    NEWSHIFTSLOTS = [
        {
            "name": "Käsetheke",
            "weekday": MONDAY,
            "start_time": "13:45:00",
            "num_of_persons": 2,
        },
        {
            "name": "Käsetheke",
            "weekday": WEDNESDAY,
            "start_time": "13:45:00",
            "num_of_persons": 2,
        },
        {
            "name": "Käsetheke",
            "weekday": SATURDAY,
            "start_time": "08:15:00",
            "num_of_persons": 2,
        },
    ]

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def handle(self, *args, **options):
        for new_slot in self.NEWSHIFTSLOTS:
            shifts = ShiftTemplate.objects.filter(
                weekday=new_slot["weekday"], start_time=new_slot["start_time"]
            )

            for shift_template in shifts:
                print(
                    "Found the suitable shift with ID:"
                    + str(shift_template.id)
                    + ", group_id: "
                    + str(shift_template.group)
                )

                existing_slots = ShiftSlotTemplate.objects.filter(
                    name=new_slot["name"], shift_template=shift_template
                )

                if len(existing_slots) < 2:
                    needed_slots = new_slot["num_of_persons"] - len(existing_slots)
                    for i in range(0, needed_slots):
                        print(
                            "Create new slot template for weekday "
                            + str(new_slot["weekday"])
                        )
                        self.create_new_shift_slot_template(
                            new_slot["name"], shift_template
                        )
                else:
                    print(
                        "Slot template already exists for weekday "
                        + str(new_slot["weekday"])
                    )

    def create_new_shift_slot_template(self, name, shift_template):
        shift_slot = ShiftSlotTemplate(
            name=name, optional=False, shift_template=shift_template
        )
        shift_slot.save()
