import pytest
from django.test import SimpleTestCase

from tapir.core.tapir_email_base import get_mail_classes


class TapirEmailBase:
    pass


class MailClassA(TapirEmailBase):
    enabled_by_default = True
    optional = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_a"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class A"


class MailClassB(TapirEmailBase):
    enabled_by_default = False
    optional = True

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_b"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class B"


class MailClassC(TapirEmailBase):
    enabled_by_default = True
    optional = True

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_class_c"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Class C"


class TestGetMailClass(SimpleTestCase):
    # Tests
    def test_getMailClass_both(self):
        result = get_mail_classes(
            enabled_by_default="both",
            optional="both",
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        assert result == [MailClassA, MailClassB, MailClassC]

    def test_getMailClass_enabled_by_default_true(self):
        result = get_mail_classes(
            enabled_by_default=True,
            optional="both",
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        assert result == [MailClassA, MailClassC]

    def test_getMailClass_enabled_by_default_false(self):
        result = get_mail_classes(
            enabled_by_default=False,
            optional="both",
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        assert result == [MailClassB]

    def test_getMailClass_optional_true(self):
        result = get_mail_classes(
            enabled_by_default="both",
            optional=True,
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        assert result == [MailClassB, MailClassC]

    def test_getMailClass_optional_false(self):
        result = get_mail_classes(
            enabled_by_default="both",
            optional=False,
            mail_classes=TapirEmailBase.__subclasses__(),
        )
        assert result == [MailClassA]


# Führe die Tests aus
if __name__ == "__main__":
    pytest.main()
