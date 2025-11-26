import datetime

from django.core.management import BaseCommand
from django.db import transaction

from tapir.coop.models import ShareOwner, MembershipPause
from tapir.coop.services.membership_pause_service import MembershipPauseService
from tapir.rizoma.config import GROUP_NAME_CONSUMIDORES
from tapir.rizoma.services.group_affiliation_checker import GroupAffiliationChecker


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        share_owner_ids_that_should_be_paused = set()
        share_owners_ids_to_delete = []
        share_owner_count = ShareOwner.objects.count()
        for index, share_owner in enumerate(ShareOwner.objects.all()):
            if index % 20 == 0:
                print(f"Getting group affiliations... {index}/{share_owner_count}")

            group_affiliation_status = (
                GroupAffiliationChecker.is_member_affiliation_to_group_active(
                    external_id=share_owner.external_id,
                    group_name=GROUP_NAME_CONSUMIDORES,
                )
            )

            if group_affiliation_status is None:
                share_owners_ids_to_delete.append(share_owner.external_id)
            elif not group_affiliation_status:
                share_owner_ids_that_should_be_paused.add(share_owner.id)

        self.delete_share_owners(share_owners_ids_to_delete)

        share_owner_ids_with_active_pause = set(
            MembershipPause.objects.active_temporal().values_list(
                "share_owner_id", flat=True
            )
        )
        self.create_new_pauses(
            share_owner_ids_with_active_pause=share_owner_ids_with_active_pause,
            share_owner_ids_that_should_be_paused=share_owner_ids_that_should_be_paused,
        )
        self.end_old_pauses(
            share_owner_ids_with_active_pause=share_owner_ids_with_active_pause,
            share_owner_ids_that_should_be_paused=share_owner_ids_that_should_be_paused,
        )

    @classmethod
    def delete_share_owners(cls, share_owners_ids_to_delete: list[int]):
        share_owners_to_delete = ShareOwner.objects.filter(
            id__in=share_owners_ids_to_delete
        )
        if share_owners_to_delete.count() > 0:
            print(
                f"Deleting the following members because they are not in {GROUP_NAME_CONSUMIDORES} anymore: {share_owners_to_delete}"
            )
        else:
            print("No member needs to be deleted")
        ShareOwner.objects.filter(id__in=share_owners_ids_to_delete).delete()

    @classmethod
    def create_new_pauses(
        cls,
        share_owner_ids_that_should_be_paused: set[int],
        share_owner_ids_with_active_pause: set[int],
    ):
        pauses_to_create = []
        for share_owner_id in share_owner_ids_that_should_be_paused.difference(
            share_owner_ids_with_active_pause
        ):
            if share_owner_id not in share_owner_ids_with_active_pause:
                pauses_to_create.append(
                    MembershipPause(
                        share_owner_id=share_owner_id,
                        description=f"Member is in the {GROUP_NAME_CONSUMIDORES} group but inactive",
                        start_date=datetime.date.today(),
                        end_date=None,
                    )
                )

        new_pauses = MembershipPause.objects.bulk_create(pauses_to_create)
        if len(new_pauses) > 0:
            print(
                f"The following pause have been created because the members are inactive: {new_pauses}"
            )
        else:
            print("No pause needs to be created")

        for pause in new_pauses:
            MembershipPauseService.on_pause_created_or_updated(pause=pause, actor=None)

    @classmethod
    def end_old_pauses(
        cls,
        share_owner_ids_that_should_be_paused: set[int],
        share_owner_ids_with_active_pause: set[int],
    ):
        pauses_to_update = MembershipPause.objects.filter(
            share_owner_id__in=share_owner_ids_with_active_pause.difference(
                share_owner_ids_that_should_be_paused
            )
        )
        pauses_to_update.update(
            end_date=datetime.date.today() - datetime.timedelta(days=1)
        )
        if pauses_to_update.count() > 0:
            print(
                f"The following pauses have been ended because the members are active again: {pauses_to_update}"
            )
        else:
            print("No pause needs to be ended")
