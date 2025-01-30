import datetime
from abc import ABC, abstractmethod

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner


class BaseDataProvider(ABC):
    @staticmethod
    def raise_not_implemented():
        raise NotImplementedError(
            "Children of BaseDataProvider must implement this method"
        )

    @classmethod
    @abstractmethod
    def get_display_name(cls):
        cls.raise_not_implemented()

    @classmethod
    @abstractmethod
    def get_description(cls):
        cls.raise_not_implemented()

    @classmethod
    @abstractmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        cls.raise_not_implemented()
