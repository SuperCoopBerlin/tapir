from typing import List, Type

from tapir.core.mail_option import MailOption
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase


class MailClassesService:
    @staticmethod
    def get_mail_classes(
        mail_option: MailOption | List[MailOption] = None,
        mail_classes: List[Type[TapirEmailBuilderBase]] = None,
    ) -> List[Type[TapirEmailBuilderBase]]:
        """
        default="both" returns both, default and non-default mails.
        default=False returns mails not being sent by default
        """

        if mail_classes is None:
            mail_classes = TapirEmailBuilderBase.__subclasses__()

        if isinstance(mail_option, list):
            return [mail for mail in mail_classes if mail.option in mail_option]

        return [mail for mail in mail_classes if mail.option == mail_option]
