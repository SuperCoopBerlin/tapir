from __future__ import annotations

from enum import Enum


class MailOption(Enum):
    OPTIONAL_ENABLED = "optional and enabled by default"
    OPTIONAL_DISABLED = "optional and disabled by default"
    MANDATORY = "mandatory"

    def is_optional(self) -> bool:
        return self in {MailOption.OPTIONAL_ENABLED, MailOption.OPTIONAL_DISABLED}

    @staticmethod
    def get_optional_options() -> list:
        return [MailOption.OPTIONAL_ENABLED, MailOption.OPTIONAL_DISABLED]

    @staticmethod
    def get_all_options() -> list:
        return list(MailOption)

    def __str__(self):
        return f"This Mail is {self.name}"
