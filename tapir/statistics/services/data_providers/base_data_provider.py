from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import Dict, Type

from django.db.models import QuerySet

from tapir.coop.models import ShareOwner

data_providers: Dict[str, Type[BaseDataProvider]] = {}


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

    @staticmethod
    def register_data_provider(data_provider: Type[BaseDataProvider]):
        data_providers[data_provider.__name__] = data_provider
