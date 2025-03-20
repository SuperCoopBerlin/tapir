from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider


class DataProviderEveryone(BaseDataProvider):
    @classmethod
    def get_display_name(cls):
        return _("Everyone")

    @classmethod
    def get_description(cls):
        return _("Every past, present or future members. Anyone that is in the system.")

    @classmethod
    def get_queryset(cls, _) -> QuerySet[ShareOwner]:
        return ShareOwner.objects.all()
