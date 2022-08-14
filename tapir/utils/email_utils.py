from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import translation

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.settings import COOP_NAME


class EmailUtils:
    @staticmethod
    def get_email_from_template(
        member: ShareOwner | TapirUser,
        subject_template_names: list,
        email_template_names: list,
        extra_context: dict,
    ):
        if isinstance(member, ShareOwner):
            share_owner = member
            member_infos = share_owner.get_info()
            tapir_user = share_owner.user
        else:
            share_owner = member.share_owner if hasattr(member, "share_owner") else None
            member_infos = member
            tapir_user = member

        context = {
            "share_owner": share_owner,
            "tapir_user": tapir_user,
            "member_infos": member_infos,
            "coop_name": COOP_NAME,
        } | extra_context  # '|' is the union operator for dictionaries.

        with translation.override(member_infos.preferred_language):
            subject = loader.render_to_string(subject_template_names, context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            body = loader.render_to_string(email_template_names, context)
        email = EmailMultiAlternatives(subject, body, to=[member_infos.email])
        email.content_subtype = "html"

        return email
