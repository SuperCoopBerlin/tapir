from typing import List

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase


class TapirAccountCreatedEmail(TapirEmailBase):
    def __init__(self, tapir_user: TapirUser):
        super().__init__()
        self.tapir_user = tapir_user

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.accounts.tapir_account_created"

    @classmethod
    def get_name(cls) -> str:
        return _("Tapir account created")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent to a member when the accounts gets created.")

    def get_subject_templates(self) -> List:
        return [
            "coop/email/tapir_account_created.subject.html",
            "coop/email/tapir_account_created.subject.default.html",
        ]

    def get_body_templates(self) -> List:
        return [
            "coop/email/tapir_account_created.body.html",
            "coop/email/tapir_account_created.body.default.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "site_url": settings.SITE_URL,
            "uid": urlsafe_base64_encode(force_bytes(self.tapir_user.pk)),
            "token": default_token_generator.make_token(self.tapir_user),
        }

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
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
