from typing import List, Type

from tapir.accounts.models import OptionalMails, TapirUser
from tapir.core.mail_option import MailOption
from tapir.core.services.mail_classes_service import MailClassesService
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase


class OptionalMailsForUserService:
    @staticmethod
    def get_optional_mail_ids_user_will_receive(user: TapirUser) -> List[str]:
        """
        Mails which are either
        A) optional but enabled by default or
        B) optional, not enabled by default but still wanted by user

        :return unique mail-ids from both lists
        """
        user_mails_wanted = list(
            OptionalMails.objects.filter(user=user, choice=True).values_list(
                "mail_id", flat=True
            )
        )
        user_mails_not_wanted = list(
            OptionalMails.objects.filter(user=user, choice=False).values_list(
                "mail_id", flat=True
            )
        )
        other_optional_mails = [
            mail_class.get_unique_id()
            for mail_class in MailClassesService.get_mail_classes(
                MailOption.OPTIONAL_ENABLED
            )
            if mail_class.get_unique_id() not in user_mails_not_wanted
        ]

        optional_mails = other_optional_mails + user_mails_wanted
        return list(set(optional_mails))

    @staticmethod
    def user_wants_to_or_has_to_receive_mail(
        user: TapirUser, mail_class: Type[TapirEmailBuilderBase]
    ) -> bool:
        return mail_class.option == MailOption.MANDATORY or (
            mail_class.get_unique_id()
            in OptionalMailsForUserService.get_optional_mail_ids_user_will_receive(user)
        )
