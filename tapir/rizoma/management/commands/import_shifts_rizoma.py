import csv
import datetime

from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from icecream import ic

from tapir.accounts.models import TapirUser
from tapir.shifts.management.commands.generate_shifts import GENERATE_UP_TO
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    ShiftSlotTemplate,
    Shift,
    ShiftAttendanceTemplate,
)
from tapir.shifts.utils import generate_shifts_up_to
from tapir.utils.expection_utils import TapirException


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        ShiftTemplate.objects.all().delete()
        Shift.objects.all().delete()

        shift_data = self.build_shift_data(options["file_name"])
        shift_templates = self.create_shift_templates(shift_data)
        grouped_shift_templates = self.group_shift_templates(shift_templates)
        self.create_slot_template(shift_data, grouped_shift_templates)
        self.create_attendance_templates(shift_data)

        generate_shifts_up_to(timezone.now().date() + GENERATE_UP_TO)

    @staticmethod
    def create_shift_templates(shift_data):
        all_shift_templates = []
        for week_group, by_day_index in shift_data.items():
            for day_index, by_start_time in by_day_index.items():
                for start_time, by_slot_name in by_start_time.items():
                    any_slot = list(by_slot_name.values())[0]
                    all_shift_templates.append(
                        ShiftTemplate(
                            group=week_group,
                            name="Test Rizoma",
                            weekday=day_index,
                            start_time=start_time,
                            end_time=any_slot["end_time"],
                            start_date=any_slot["start_date"],
                        )
                    )

        return ShiftTemplate.objects.bulk_create(all_shift_templates)

    @staticmethod
    def group_shift_templates(all_shift_templates):
        shift_templates_by_week_group = {}
        for shift_template in all_shift_templates:
            if shift_template.group not in shift_templates_by_week_group.keys():
                shift_templates_by_week_group[shift_template.group] = {}
            shift_templates_by_day_index = shift_templates_by_week_group[
                shift_template.group
            ]

            if shift_template.weekday not in shift_templates_by_day_index.keys():
                shift_templates_by_day_index[shift_template.weekday] = {}
            shift_templates_by_start_time = shift_templates_by_day_index[
                shift_template.weekday
            ]

            shift_templates_by_start_time[shift_template.start_time] = shift_template

        return shift_templates_by_week_group

    @staticmethod
    def create_slot_template(shift_data, grouped_shift_templates):
        all_slot_templates = []
        for week_group, by_day_index in shift_data.items():
            for day_index, by_start_time in by_day_index.items():
                for start_time, by_slot_name in by_start_time.items():
                    shift_template = grouped_shift_templates[week_group][day_index][
                        start_time
                    ]
                    for slot_name, slot_data in by_slot_name.items():
                        for _ in range(slot_data["nb_slots"]):
                            all_slot_templates.append(
                                ShiftSlotTemplate(
                                    name=slot_name, shift_template=shift_template
                                )
                            )

        return ShiftSlotTemplate.objects.bulk_create(all_slot_templates)

    @staticmethod
    def build_shift_data(file_name):
        portuguese_day_name_to_day_index = {
            "Segunda": 0,
            "Terça": 1,
            "Quarta": 2,
            "Quinta": 3,
            "Sexta": 4,
            "Sabado": 5,
            "Domingo": 6,
        }

        week_groups_by_name = {
            name: ShiftTemplateGroup.objects.get_or_create(name=name)[0]
            for name in ["A", "B", "C", "D"]
        }

        by_week_group = {}
        with open(file_name) as csvfile:
            for row in csv.reader(csvfile):
                if row[1] != "Regular":
                    continue

                week_group = week_groups_by_name[row[3]]
                day_index = portuguese_day_name_to_day_index[row[2]]
                start_time_as_string = row[4].split(":")
                start_time = datetime.time(
                    hour=int(start_time_as_string[0]),
                    minute=int(start_time_as_string[1]),
                )
                end_time_as_string = row[6].split(":")
                end_time = datetime.time(
                    hour=int(end_time_as_string[0]), minute=int(end_time_as_string[1])
                )
                slot_name = row[7]
                name_of_the_registered_members = row[8]
                nb_slots = int(row[10])
                start_date = datetime.datetime.strptime(row[13], "%d/%m/%Y %H:%M")

                if week_group not in by_week_group.keys():
                    by_week_group[week_group] = {}
                by_day_index = by_week_group[week_group]
                if day_index not in by_day_index.keys():
                    by_day_index[day_index] = {}
                by_start_time = by_week_group[week_group][day_index]
                if start_time not in by_start_time.keys():
                    by_start_time[start_time] = {}
                by_slot_name = by_start_time[start_time]
                if slot_name not in by_slot_name.keys():
                    by_slot_name[slot_name] = {
                        "name_of_the_registered_members": name_of_the_registered_members,
                        "nb_slots": nb_slots,
                        "start_date": start_date,
                        "end_time": end_time,
                    }

        return by_week_group

    @classmethod
    def create_attendance_templates(cls, shift_data):
        members_by_name = {
            f"{tapir_user.first_name} {tapir_user.last_name}".casefold(): tapir_user
            for tapir_user in TapirUser.objects.all()
        }

        attendance_templates = []
        slot_ids_already_taken = []
        for week_group, by_day_index in shift_data.items():
            for day_index, by_start_time in by_day_index.items():
                for start_time, by_slot_name in by_start_time.items():
                    for slot_name, slot_data in by_slot_name.items():
                        for member_name in slot_data[
                            "name_of_the_registered_members"
                        ].split(","):
                            member_name = member_name.strip().casefold()
                            if member_name == "":
                                continue
                            if member_name not in members_by_name.keys():
                                ic("Unknown member name", member_name, slot_data)
                                continue

                            attendance_templates.append(
                                cls.build_attendance_template(
                                    day_index,
                                    member_name,
                                    members_by_name,
                                    slot_data,
                                    slot_ids_already_taken,
                                    slot_name,
                                    start_time,
                                    week_group,
                                )
                            )

        return ShiftAttendanceTemplate.objects.bulk_create(attendance_templates)

    @classmethod
    def build_attendance_template(
        cls,
        day_index,
        member_name,
        members_by_name,
        slot_data,
        slot_ids_already_taken,
        slot_name,
        start_time,
        week_group,
    ):
        slot = (
            ShiftSlotTemplate.objects.filter(
                shift_template__group=week_group,
                shift_template__weekday=day_index,
                shift_template__start_time=start_time,
                name=slot_name,
            )
            .exclude(id__in=slot_ids_already_taken)
            .first()
        )
        if slot is None:
            ic(
                week_group,
                day_index,
                start_time,
                slot_name,
                slot_data,
            )
            raise TapirException("No available slot for: " + member_name)
        slot_ids_already_taken.append(slot.id)
        return ShiftAttendanceTemplate(
            user=members_by_name[member_name],
            slot_template=slot,
        )
