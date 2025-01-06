from typing import List, Tuple

from tapir.core.mail_option import MailOption
from tapir.core.services.mail_classes_service import MailClassesService


class OptionalMailChoicesService:
    @staticmethod
    def get_optional_mail_choices() -> List[Tuple[str, str]]:
        # this has to be a function so that choices has a callable and is refreshed whenever the form is called
        return [
            (mail.get_unique_id(), mail.get_name())
            for mail in MailClassesService.get_mail_classes(
                mail_option=MailOption.get_optional_options()
            )
        ]

    @staticmethod
    def get_mandatory_mail_choices() -> List[Tuple[str, str]]:
        # this has to be a function so that choices has a callable and is refreshed whenever the form is called
        return [
            (mail.get_unique_id(), mail.get_name())
            for mail in MailClassesService.get_mail_classes(
                mail_option=MailOption.MANDATORY
            )
        ]
