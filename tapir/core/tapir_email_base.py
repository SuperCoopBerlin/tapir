from __future__ import annotations

from enum import Enum
from typing import List, Type, TYPE_CHECKING, Dict

from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import translation

from tapir import settings

if TYPE_CHECKING:
    # ignore at runtime to avoid circular import
    from tapir.accounts.models import TapirUser
    from tapir.coop.models import ShareOwner
from tapir.log.models import EmailLogEntry

all_emails: Dict[str, Type[TapirEmailBase]] = {}


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


def get_mail_classes(
    mail_option: MailOption | List[MailOption] = None,
    mail_classes: List[Type[TapirEmailBase]] = None,
) -> List[Type[TapirEmailBase]]:
    """
    default="both" returns both, default and non-default mails.
    default=False returns mails not being sent by default
    """
    if mail_classes is None:
        mail_classes = TapirEmailBase.__subclasses__()

    if isinstance(mail_option, list):
        return [mail for mail in mail_classes if mail.option in mail_option]

    return [mail for mail in mail_classes if mail.option == mail_option]


class TapirEmailBase:
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
    def get_dummy_version(cls) -> TapirEmailBase | None:
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

    def send_to_share_owner(
        self, actor: TapirUser | User | None, recipient: ShareOwner
    ):
        self.__send(
            actor=actor,
            share_owner=recipient,
            member_infos=recipient.get_info(),
            tapir_user=recipient.user,
        )

    def user_wants_to_or_has_to_receive_mail(self, user: TapirUser):
        return (
            self.get_unique_id() in user.get_optional_mail_ids_user_will_receive()
        ) or (self.option == MailOption.MANDATORY)

    def send_to_tapir_user(self, actor: TapirUser | User | None, recipient: TapirUser):
        if not self.user_wants_to_or_has_to_receive_mail(user=recipient):
            return

        self.__send(
            actor=actor,
            share_owner=(
                recipient.share_owner if hasattr(recipient, "share_owner") else None
            ),
            member_infos=recipient,
            tapir_user=recipient,
        )

    @staticmethod
    def include_email_body_in_log_entry():
        """
        Overwrite this in your subclass with 'return False', if you don't want the mail body to be in your log-entry,
        for example if it contains sensitive data.
        """
        return True

    def create_log_entry(self, email, actor, tapir_user, share_owner):
        if not self.include_email_body_in_log_entry():
            email = None
        EmailLogEntry().populate(
            email_id=self.get_unique_id(),
            email_message=email,
            actor=actor,
            tapir_user=tapir_user,
            share_owner=share_owner,
        ).save()

    def __send(
        self,
        actor: TapirUser | User,
        share_owner: ShareOwner,
        member_infos,
        tapir_user: TapirUser,
    ):
        context = self.get_full_context(
            share_owner=share_owner, member_infos=member_infos, tapir_user=tapir_user
        )

        with translation.override(member_infos.preferred_language):
            subject = self.get_subject(context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            context |= {"subject": subject}
            body = self.get_body(context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            to=[member_infos.email],
            from_email=self.get_from_email(),
            attachments=self.get_attachments(),
        )

        email.content_subtype = "html"
        email.send()
        self.create_log_entry(
            email=email, actor=actor, tapir_user=tapir_user, share_owner=share_owner
        )

    @classmethod
    def register_email(cls, mail_class: Type[TapirEmailBase]):
        all_emails[mail_class.get_unique_id()] = mail_class
