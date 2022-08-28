from typing import List

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.core.tapir_email_base import TapirEmailBase, all_emails


class TapirAccountCreatedEmail(TapirEmailBase):
    tapir_user = None

    def __init__(self, tapir_user: TapirUser):
        self.tapir_user = tapir_user

    @staticmethod
    def get_unique_id() -> str:
        return "tapir.accounts.tapir_account_created"

    @staticmethod
    def get_name() -> str:
        return _("Tapir account created")

    @staticmethod
    def get_description() -> str:
        return _("Sent to a member when the accounts gets created.")

    @staticmethod
    def get_subject_templates() -> List:
        return [
            "accounts/email/tapir_account_created.subject.html",
            "accounts/email/tapir_account_created.subject.default.html",
        ]

    @staticmethod
    def get_body_templates() -> List:
        return [
            "accounts/email/tapir_account_created.body.html",
            "accounts/email/tapir_account_created.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "site_url": settings.SITE_URL,
            "uid": urlsafe_base64_encode(force_bytes(self.tapir_user)),
            "token": default_token_generator.make_token(self.tapir_user),
        }


all_emails[TapirAccountCreatedEmail.get_unique_id()] = TapirAccountCreatedEmail
