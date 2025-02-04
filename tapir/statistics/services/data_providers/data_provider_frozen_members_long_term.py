import datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import UpdateShiftUserDataLogEntry
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider
from tapir.statistics.services.data_providers.data_provider_frozen_members import (
    DataProviderFrozenMembers,
)


class DataProviderFrozenMembersLongTerm(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Long-term frozen members")

    @classmethod
    def get_description(cls):
        return _(
            'Members that are frozen since more than 180 days (roughly 6 month). Long-term frozen members are included in the "Frozen members" dataset'
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        share_owners_frozen = DataProviderFrozenMembers.get_queryset(reference_time)
        tapir_user_frozen_ids = list(
            share_owners_frozen.values_list("user__id", flat=True)
        )

        long_term_frozen_ids = []
        for tapir_user_id in tapir_user_frozen_ids:
            status_change_log_entry = (
                UpdateShiftUserDataLogEntry.objects.filter(
                    user__id=tapir_user_id,
                    created_date__lte=reference_time,
                    new_values__is_frozen="True",
                )
                .order_by("-created_date")
                .first()
            )

            if not status_change_log_entry:
                # could not find any log entry, we assume the member is frozen long-term
                long_term_frozen_ids.append(tapir_user_id)
                continue

            if (reference_time - status_change_log_entry.created_date).days > 30 * 6:
                long_term_frozen_ids.append(tapir_user_id)

        return ShareOwner.objects.filter(user__id__in=long_term_frozen_ids)
