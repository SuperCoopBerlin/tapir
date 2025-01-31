import datetime

from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAttendance, ShiftExemption
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderExemptedMembersThatWork(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Exempted members that work")

    @classmethod
    def get_description(cls):
        return _(
            "Counting all exempted members (ignoring if they are frozen or investing) that actually did a shift in the past 60 days. Just registering to the shift doesn't count, the attendance must be confirmed."
        )

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        reference_date = reference_time.date()

        exemptions = ShiftExemption.objects.active_temporal(reference_date)
        members_exempted = ShareOwner.objects.filter(
            user__shift_user_data__shift_exemptions__in=exemptions
        ).distinct()
        members_exempted_ids = list(members_exempted.values_list("id", flat=True))

        members_that_did_a_shift_ids = cls.get_ids_of_members_that_did_a_shift_lately(
            reference_time
        )

        all_criteria = Q()
        for id_list in [members_exempted_ids, members_that_did_a_shift_ids]:
            all_criteria &= Q(id__in=id_list)

        return ShareOwner.objects.filter(all_criteria)

    @staticmethod
    def get_ids_of_members_that_did_a_shift_lately(reference_time):
        return list(
            ShiftAttendance.objects.filter(
                state=ShiftAttendance.State.DONE,
                slot__shift__start_time__gte=reference_time
                - datetime.timedelta(days=60),
                slot__shift__start_time__lte=reference_time,
            ).values_list("user__share_owner__id", flat=True)
        )
