from __future__ import annotations

from typing import List, Type, TYPE_CHECKING, Dict

from django.contrib.auth.models import User
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


def get_all_emails(default=True) -> List[str]:
    if default is None:
        return get_all_default_emails()
    else:
        return [key for key, value in all_emails.items()]


def get_all_default_emails() -> List[str]:
    return [key for key, value in all_emails.items() if value.default is True]


EMAIL_CHOICES = [
    ("tapir.accounts.create_account_reminder", "Konto erstellen Erinnerung"),
    ("tapir.shifts.shift_missed", "Schicht versäumt"),
    ("tapir.shifts.shift_reminder", "Schicht-Erinnerung"),
    ("tapir.shifts.stand_in_found", "Vertretung gefunden"),
    ("tapir.shifts.member_frozen", "Shift status set to frozen"),
    ("tapir.shifts.freeze_warning", "Freeze warning"),
    ("tapir.shifts.unfreeze_notification", "Unfreeze Notification"),
    ("tapir.coop.extra_shares_confirmation", "Extra shares bought"),
    (
        "tapir.coop.membership_confirmation.active",
        "Mitgliedsbestätigung für aktive Mitglieder",
    ),
    (
        "tapir.coop.membership_confirmation.investing",
        "Mitgliedsbestätigung für investierende Mitglieder",
    ),
    ("tapir.accounts.tapir_account_created", "Tapir-Konto erstellt"),
    ("tapir.coop.co_purchaser_updated_mail", "Mitkäufer*in aktualisiert"),
    (
        "tapir.shifts.shift_understaffed_mail",
        "Schicht mit Personalmangel (automatische Warnung)",
    ),
]


class TapirEmailBase:
    default = True
    mandatory = True

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

    def send_to_share_owner(self, actor: User | None, recipient: ShareOwner):
        self.__send(
            actor=actor,
            share_owner=recipient,
            member_infos=recipient.get_info(),
            tapir_user=recipient.user,
        )

    def send_to_tapir_user(self, actor: User | None, recipient: TapirUser):
        self.__send(
            actor=actor,
            share_owner=recipient.share_owner
            if hasattr(recipient, "share_owner")
            else None,
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
        actor: User,
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
