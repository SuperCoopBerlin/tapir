import csv
import datetime

from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from icecream import ic

from tapir.accounts.models import TapirUser
from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    ShiftSlotTemplate,
    Shift,
    ShiftAttendanceTemplate,
    ShiftUserCapability,
    ShiftUserCapabilityTranslation,
    CreateShiftAttendanceTemplateLogEntry,
)
from tapir.shifts.utils import generate_shifts_up_to
from tapir.utils.expection_utils import TapirException
from tapir.utils.shortcuts import get_monday


class Command(BaseCommand):
    QUALIFICATION_TRANSLATIONS = {
        "en": {"Caixa": "Cashier", "Mercearia": "Shop"},
        "de": {"Caixa": "Kasse", "Mercearia": "Laden"},
    }

    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        if FeatureFlag.get_flag_value(FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS):
            answer = input(
                "Invites via Google calendar are enabled, importing shifts will send invites by mail, are you sure you want to continue? (y/n)"
            )
            if answer.lower() not in ["y", "yes"]:
                print("Cancelled import")
                return

        ShiftTemplate.objects.all().delete()
        Shift.objects.filter(
            start_time__date__gte=get_monday(timezone.now().date())
        ).delete()

        shift_data = self.build_shift_data(options["file_name"])
        shift_templates = self.create_shift_templates(shift_data)
        grouped_shift_templates = self.group_shift_templates(shift_templates)
        self.create_slot_template(shift_data, grouped_shift_templates)
        self.assign_shift_user_capabilities_to_slot_templates()
        self.create_attendance_templates(shift_data)
        self.add_capabilities_to_users()

        generate_shifts_up_to(timezone.now().date() + datetime.timedelta(days=30))

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
                            name="Rizoma",
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

    @classmethod
    def create_slot_template(cls, shift_data, grouped_shift_templates):
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

    @classmethod
    def assign_shift_user_capabilities_to_slot_templates(cls):
        existing_qualifications = {
            capability.shiftusercapabilitytranslation_set.get(
                language="pt"
            ).name: capability
            for capability in ShiftUserCapability.objects.all()
        }
        many_to_many_links = []
        for slot_template in ShiftSlotTemplate.objects.all():
            capability = cls.get_or_create_capability(
                portuguese_name=slot_template.name,
                existing_qualifications=existing_qualifications,
            )
            many_to_many_links.append(
                ShiftSlotTemplate.required_capabilities.through(
                    shiftusercapability=capability, shiftslottemplate=slot_template
                )
            )

        ShiftSlotTemplate.required_capabilities.through.objects.bulk_create(
            many_to_many_links
        )

    @classmethod
    def get_or_create_capability(
        cls, portuguese_name: str, existing_qualifications: dict
    ) -> ShiftUserCapability:
        if portuguese_name in existing_qualifications.keys():
            return existing_qualifications[portuguese_name]

        capability = ShiftUserCapability.objects.create()
        translations = [
            ShiftUserCapabilityTranslation(
                capability=capability, language="pt", name=portuguese_name
            )
        ]
        for language in cls.QUALIFICATION_TRANSLATIONS.keys():
            translated_name = cls.QUALIFICATION_TRANSLATIONS[language].get(
                portuguese_name, None
            )
            if translated_name is not None:
                translations.append(
                    ShiftUserCapabilityTranslation(
                        capability=capability,
                        language=language,
                        name=translated_name,
                    )
                )

        ShiftUserCapabilityTranslation.objects.bulk_create(translations)

        existing_qualifications[portuguese_name] = capability

        return capability

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
        count = 0
        with open(file_name) as csvfile:
            for row in csv.reader(csvfile):
                count +=1
                if row[1] != "Regular":
                    continue
                
                print(f"Parsing line {count}")

                week_group = week_groups_by_name[row[3]]
                day_index = portuguese_day_name_to_day_index[row[2]]
                start_time_as_string = row[4].split(":")
                start_time = datetime.time(
                    hour=int(start_time_as_string[0]),
                    minute=int(start_time_as_string[1]),
                )
                end_time_as_string = row[5].split(":")
                end_time = datetime.time(
                    hour=int(end_time_as_string[0]), minute=int(end_time_as_string[1])
                )
                slot_name = row[6]
                name_of_the_registered_members = row[7]
                nb_slots = int(row[9])
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
                                    slot_ids_already_taken,
                                    slot_name,
                                    start_time,
                                    week_group,
                                )
                            )
        attendance_templates = ShiftAttendanceTemplate.objects.bulk_create(
            attendance_templates
        )
        for attendance_template in attendance_templates:
            CreateShiftAttendanceTemplateLogEntry().populate(
                actor=None,
                tapir_user=attendance_template.user,
                shift_attendance_template=attendance_template,
            ).save()

    @classmethod
    def build_attendance_template(
        cls,
        day_index,
        member_name,
        members_by_name,
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
            raise TapirException("No available slot for: " + member_name)
        slot_ids_already_taken.append(slot.id)
        return ShiftAttendanceTemplate(
            user=members_by_name[member_name],
            slot_template=slot,
        )

    @classmethod
    def add_capabilities_to_users(cls):
        existing_qualifications = {
            capability.shiftusercapabilitytranslation_set.get(
                language="pt"
            ).name: capability
            for capability in ShiftUserCapability.objects.all()
        }
        for attendance_template in ShiftAttendanceTemplate.objects.prefetch_related(
            "user",
            "user__shift_user_data",
            "user__shift_user_data__capabilities",
            "slot_template",
        ):
            qualification = existing_qualifications[
                attendance_template.slot_template.name
            ]
            if (
                qualification
                in attendance_template.user.shift_user_data.capabilities.all()
            ):
                continue
            attendance_template.user.shift_user_data.capabilities.add(qualification)
