from typing import List

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwner, DraftUser
from tapir.core.tapir_email_base import TapirEmailBase


class CreateAccountReminderEmail(TapirEmailBase):
    def __init__(self, tapir_user: DraftUser):
        super().__init__()
        self.draft_user = tapir_user

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.accounts.create_account_reminder"

    @classmethod
    def get_name(cls) -> str:
        return _("Create account reminder")

    @classmethod
    def get_description(cls) -> str:
        return _(
            "Sent to active member if they haven't created the account 1 month after becoming member."
        )

    def get_subject_templates(self) -> List:
        return [
            "accounts/email/create_account_reminder.subject.html",
            "accounts/email/create_account_reminder.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "accounts/email/create_account_reminder.body.html",
            "accounts/email/create_account_reminder.body.default.html",
        ]

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        # TODO fix it
        share_owner = ShareOwner.objects.filter(user__isnull=False).order_by("?")[0]
        mail = cls(tapir_user=share_owner.user)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail

    @staticmethod
    def include_email_body_in_log_entry():
        return False
