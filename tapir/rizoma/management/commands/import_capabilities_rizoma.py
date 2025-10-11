import csv

from django.core.management import BaseCommand
from django.db import transaction

from tapir.shifts.models import (
    ShiftUserData,
    ShiftUserCapabilityTranslation,
)
from tapir.utils.expection_utils import TapirException


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        shift_user_capabilities = self.build_user_capabilities(options["file_name"])
        ShiftUserData.capabilities.through.objects.bulk_create(shift_user_capabilities)

    @staticmethod
    def build_user_capabilities(file_name) -> list[ShiftUserData.capabilities.through]:
        shift_user_data_by_member_id = {
            shift_user_data.user.share_owner.id: shift_user_data
            for shift_user_data in ShiftUserData.objects.filter(
                user__share_owner__isnull=False
            ).prefetch_related("user", "user__share_owner")
        }
        capabilities_by_portuguese_name = {
            translation.name.casefold(): translation.capability
            for translation in ShiftUserCapabilityTranslation.objects.filter(
                language="pt"
            )
        }

        user_capabilities = []

        count = 0
        with open(file_name) as csvfile:
            for row in csv.reader(csvfile):
                count +=1
                print(f"Parsing line {count}")
                member_id = int(row[2])
                capabilities_as_string = row[4].split(",")
                capabilities_as_string = [
                    capability.replace("Flex / Flex", "").strip().casefold()
                    for capability in capabilities_as_string
                ]
                for capability_name in capabilities_as_string:
                    if capability_name not in capabilities_by_portuguese_name.keys():
                        raise TapirException(
                            "Can't find capability with name: " + capability_name
                        )
                    if member_id not in shift_user_data_by_member_id.keys():
                        raise TapirException(f"Can't find member with id: {member_id}")

                    user_capabilities.append(
                        ShiftUserData.capabilities.through(
                            shiftusercapability=capabilities_by_portuguese_name[
                                capability_name
                            ],
                            shiftuserdata=shift_user_data_by_member_id[member_id],
                        )
                    )

        return user_capabilities
