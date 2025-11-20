from django.core.management import BaseCommand

from tapir.coop.models import ShareOwner
from tapir.rizoma.config import GROUP_NAME_CONSUMIDORES
from tapir.rizoma.services.group_affiliation_checker import GroupAffiliationChecker


class Command(BaseCommand):
    def handle(self, *args, **options):
        share_owner_ids_to_delete = []
        for share_owner in ShareOwner.objects.all():
            if not GroupAffiliationChecker.is_member_affiliation_to_group_active(
                external_id=share_owner.external_id, group_name=GROUP_NAME_CONSUMIDORES
            ):
                share_owner_ids_to_delete.append(share_owner.id)

        ShareOwner.objects.filter(id__in=share_owner_ids_to_delete).delete()
