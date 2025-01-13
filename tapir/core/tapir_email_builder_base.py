from __future__ import annotations

from typing import List, Type, TYPE_CHECKING, Dict

from django.template import loader

from tapir import settings
from tapir.core.mail_option import MailOption

if TYPE_CHECKING:
    # ignore at runtime to avoid circular import
    from tapir.accounts.models import TapirUser
    from tapir.coop.models import ShareOwner

all_emails: Dict[str, Type[TapirEmailBuilderBase]] = {}


class TapirEmailBuilderBase:
    option: MailOption = MailOption.MANDATORY

    class Meta:
        abstract = True

    def __init__(self):
        self.context = None

    @classmethod
    def get_unique_id(cls) -> str:
        raise NotImplementedError(
            f"Subclass {cls.__name__} of TapirEmail must override get_unique_id"
        )

    @classmethod
    def get_name(cls) -> str:
        raise NotImplementedError(
            f"Subclass {cls.__name__} of TapirEmail must override get_name"
        )

    @classmethod
    def get_description(cls) -> str:
        raise NotImplementedError(
            f"Subclass {cls.__name__} of TapirEmail must override get_description"
        )

    def get_subject_templates(self) -> List:
        raise NotImplementedError(
            f"Subclass {type(self).__name__} of TapirEmail must override get_subject_templates"
        )

    def get_body_templates(self) -> List:
        raise NotImplementedError(
            f"Subclass {type(self).__name__} of TapirEmail must override get_body_templates"
        )

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        raise NotImplementedError(
            f"Subclass {cls.__name__} of TapirEmail must override get_dummy_version"
        )

    def get_extra_context(self) -> dict:
        return {}

    @staticmethod
    def get_from_email() -> str:
        return settings.EMAIL_ADDRESS_MEMBER_OFFICE

    def get_attachments(self) -> List:
        return []

    def get_subject(self, context: dict) -> str:
        return loader.render_to_string(self.get_subject_templates(), context)

    def get_body(self, context: dict) -> str:
        return loader.render_to_string(self.get_body_templates(), context)

    def get_full_context(
        self,
        share_owner: ShareOwner,
        member_infos,
        tapir_user: TapirUser,
    ) -> dict:
        if self.context is None:
            self.context = {
                "share_owner": share_owner,
                "tapir_user": tapir_user,
                "member_infos": member_infos,
                "coop_name": settings.COOP_NAME,
                "coop_full_name": settings.COOP_FULL_NAME,
                "email_unique_id": self.get_unique_id(),
            } | self.get_extra_context()  # '|' is the union operator for dictionaries.

        return self.context

    @staticmethod
    def include_email_body_in_log_entry():
        """
        Overwrite this in your subclass with 'return False', if you don't want the mail body to be in your log-entry,
        for example if it contains sensitive data.
        """
        return True

    @classmethod
    def register_email(cls, mail_class: Type[TapirEmailBuilderBase]):
        all_emails[mail_class.get_unique_id()] = mail_class
