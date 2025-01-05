import pytest
from django.test import SimpleTestCase

from tapir.core.tapir_email_base import get_mail_classes, MailOption


class TapirEmailBase:
    pass


class MailClassA(TapirEmailBase):
    option = MailOption.MANDATORY

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_a"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class A"


class MailClassB(TapirEmailBase):
    option = MailOption.OPTIONAL_DISABLED

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_b"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class B"


class MailClassC(TapirEmailBase):
    option = MailOption.OPTIONAL_ENABLED

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_c"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class C"


class TestGetMailClass(SimpleTestCase):
    # Tests
    def test_getMailClass_all(self):
        result = get_mail_classes(
            mail_option=MailOption.get_all_options(),
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        self.assertEqual(result, [MailClassA, MailClassB, MailClassC])

    def test_getMailClass_enabled_by_default_true(self):
        result = get_mail_classes(
            mail_option=MailOption.OPTIONAL_ENABLED,
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        self.assertEqual(result, [MailClassC])

    def test_getMailClass_enabled_by_default_false(self):
        result = get_mail_classes(
            mail_option=MailOption.OPTIONAL_DISABLED,
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        self.assertEqual(result, [MailClassB])

    def test_getMailClass_optional_true(self):
        result = get_mail_classes(
            mail_option=MailOption.get_optional_options(),
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        self.assertEqual(result, [MailClassB, MailClassC])

    def test_getMailClass_optional_false(self):
        result = get_mail_classes(
            mail_option=MailOption.MANDATORY,
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        self.assertEqual(result, [MailClassA])


# Führe die Tests aus
if __name__ == "__main__":
    pytest.main()
