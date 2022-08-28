from typing import List

from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import translation

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.log.models import EmailLogEntry
from tapir.settings import COOP_NAME, EMAIL_ADDRESS_MEMBER_OFFICE


all_emails = {}


class TapirEmailBase:
    class Meta:
        abstract = True

    @staticmethod
    def get_unique_id() -> str:
        raise NotImplementedError(
            "Subclasses of TapirEmail must override get_unique_id"
        )

    @staticmethod
    def get_name() -> str:
        raise NotImplementedError("Subclasses of TapirEmail must override get_name")

    @staticmethod
    def get_description() -> str:
        raise NotImplementedError(
            "Subclasses of TapirEmail must override get_description"
        )

    def get_subject_templates(self) -> List:
        raise NotImplementedError(
            "Subclasses of TapirEmail must override get_subject_templates"
        )

    def get_body_templates(self) -> List:
        raise NotImplementedError(
            "Subclasses of TapirEmail must override get_body_templates"
        )

    def get_extra_context(self) -> dict:
        return {}

    def get_from_email(self) -> str:
        return EMAIL_ADDRESS_MEMBER_OFFICE

    def get_attachments(self) -> List:
        return []

    def send_to_share_owner(self, actor: TapirUser, recipient: ShareOwner):
        self.__send(
            actor=actor,
            share_owner=recipient,
            member_infos=recipient.get_info(),
            tapir_user=recipient.user,
        )

    def send_to_tapir_user(self, actor: TapirUser, recipient: TapirUser):
        self.__send(
            actor=actor,
            share_owner=recipient.share_owner
            if hasattr(recipient, "share_owner")
            else None,
            member_infos=recipient,
            tapir_user=recipient,
        )

    def __send(
        self,
        actor: TapirUser,
        share_owner: ShareOwner,
        member_infos,
        tapir_user: TapirUser,
    ):
        context = {
            "share_owner": share_owner,
            "tapir_user": tapir_user,
            "member_infos": member_infos,
            "coop_name": COOP_NAME,
        } | self.get_extra_context()  # '|' is the union operator for dictionaries.

        with translation.override(member_infos.preferred_language):
            subject = loader.render_to_string(self.get_subject_templates(), context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            body = loader.render_to_string(self.get_body_templates(), context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            to=[member_infos.email],
            from_email=self.get_from_email(),
            attachments=self.get_attachments(),
        )

        email.content_subtype = "html"
        email.send()

        log_entry = EmailLogEntry().populate(
            email_id=self.get_unique_id(),
            email_message=email,
            actor=actor,
            user=tapir_user,
            share_owner=share_owner,
        )
        log_entry.save()
