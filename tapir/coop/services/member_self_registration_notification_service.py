from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from tapir.coop.models import DraftUser
from tapir.utils.user_utils import UserUtils


class MemberSelfRegistrationNotificationService:
    @classmethod
    def send_mail_to_member_office(cls, draft_user: DraftUser):
        context = {
            "draft_user": draft_user,
            "site_url": settings.SITE_URL,
        }
        body = loader.render_to_string(
            [
                "coop/email/member_self_registration_member_office.body.html",
            ],
            context,
        )

        subject = (
            f"Neue Bewerbung aus der online Formular: {UserUtils.build_display_name(
                person=draft_user, display_type="full"
            )}"
        )
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            to=[settings.EMAIL_ADDRESS_MEMBER_OFFICE],
            from_email=settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        )
        email.content_subtype = "html"
        email.send()
