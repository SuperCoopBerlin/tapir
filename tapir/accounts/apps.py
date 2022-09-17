from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "tapir.accounts"

    def ready(self):
        from tapir.accounts.emails.tapir_account_created_email import (
            TapirAccountCreatedEmail,
        )
        from tapir.core.tapir_email_base import TapirEmailBase

        TapirEmailBase.register_email(TapirAccountCreatedEmail)
