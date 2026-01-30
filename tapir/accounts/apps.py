from django.apps import AppConfig
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tapir.accounts.config import feature_flag_open_door
from tapir.core.config import sidebar_link_groups


class AccountsConfig(AppConfig):
    name = "tapir.accounts"

    def ready(self):
        self.register_sidebar_links()
        self.register_emails()

    @staticmethod
    def register_sidebar_links():
        misc_group = sidebar_link_groups.get_group(_("Miscellaneous"), 5)

        misc_group.add_link(
            display_name=_("Open Door"),
            material_icon="lock_open",
            url=reverse_lazy("accounts:open_door_page"),
            ordering=10,
            required_feature_flag=feature_flag_open_door,
        )

    @staticmethod
    def register_emails():
        from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
        from tapir.accounts.emails.create_account_reminder_email import (
            CreateAccountReminderEmailBuilder,
        )

        TapirEmailBuilderBase.register_email(CreateAccountReminderEmailBuilder)
