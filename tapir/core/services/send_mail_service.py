from __future__ import annotations

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.utils import translation

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.core.services.optional_mails_for_user_service import (
    OptionalMailsForUserService,
)
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.log.models import EmailLogEntry


class SendMailService:
    @staticmethod
    def create_log_entry(
        email: EmailMultiAlternatives,
        actor: TapirUser | None,
        tapir_user: TapirUser,
        share_owner: ShareOwner,
        email_builder: TapirEmailBuilderBase,
    ):
        if not email_builder.include_email_body_in_log_entry():
            email = None

        EmailLogEntry().populate(
            email_id=email_builder.get_unique_id(),
            email_message=email,
            actor=actor,
            tapir_user=tapir_user,
            share_owner=share_owner,
        ).save()

    @classmethod
    def __send(
        cls,
        email_builder: TapirEmailBuilderBase,
        actor: TapirUser | User,
        share_owner: ShareOwner,
        member_infos,
        tapir_user: TapirUser,
    ):
        context = email_builder.get_full_context(
            share_owner=share_owner, member_infos=member_infos, tapir_user=tapir_user
        )

        with translation.override(member_infos.preferred_language):
            subject = email_builder.get_subject(context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            context |= {"subject": subject}
            body = email_builder.get_body(context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            to=[member_infos.email],
            from_email=email_builder.get_from_email(),
            attachments=email_builder.get_attachments(),
        )

        email.content_subtype = "html"
        email.send()
        cls.create_log_entry(
            email=email,
            actor=actor,
            tapir_user=tapir_user,
            share_owner=share_owner,
            email_builder=email_builder,
        )

    @classmethod
    def send_to_share_owner(
        cls,
        actor: TapirUser | User | None,
        recipient: ShareOwner,
        email_builder: TapirEmailBuilderBase,
    ):
        cls.__send(
            actor=actor,
            share_owner=recipient,
            member_infos=recipient.get_info(),
            tapir_user=recipient.user,
            email_builder=email_builder,
        )

    @classmethod
    def send_to_tapir_user(
        cls,
        actor: TapirUser | User | None,
        recipient: TapirUser,
        email_builder: TapirEmailBuilderBase,
    ):
        if not OptionalMailsForUserService.user_wants_to_or_has_to_receive_mail(
            user=recipient, mail_class=email_builder.__class__
        ):
            return

        cls.__send(
            actor=actor,
            share_owner=(
                recipient.share_owner if hasattr(recipient, "share_owner") else None
            ),
            member_infos=recipient,
            tapir_user=recipient,
            email_builder=email_builder,
        )
