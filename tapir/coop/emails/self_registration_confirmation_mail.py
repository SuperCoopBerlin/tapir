from django.utils.translation import gettext_lazy as _

from tapir.coop.models import DraftUser
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.settings import EMAIL_ADDRESS_MEMBER_OFFICE


class SelfRegistrationConfirmationMail(TapirEmailBuilderBase):
    def __init__(self, draft_user: DraftUser):
        super().__init__()
        self.draft_user = draft_user

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.self_registration_confirmation_mail"

    @classmethod
    def get_name(cls) -> str:
        return _("Self registration confirmation")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to a user when they register by themselves. The user is not a member yet."
        )

    def get_subject_templates(self) -> list:
        return [
            "coop/email/self_registration_confirmation.subject.html",
            "coop/email/self_registration_confirmation.subject.default.html",
        ]

    def get_body_templates(self) -> list:
        return [
            "coop/email/self_registration_confirmation.body.html",
            "coop/email/self_registration_confirmation.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "EMAIL_ADDRESS_MEMBER_OFFICE": EMAIL_ADDRESS_MEMBER_OFFICE,
            "draft_user": self.draft_user,
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        draft_user = DraftUser.objects.order_by("?").first()
        if not draft_user:
            return None

        mail = cls(draft_user=draft_user)
        mail.get_full_context(
            share_owner=None,
            member_infos=draft_user,
            tapir_user=None,
        )
        return mail
