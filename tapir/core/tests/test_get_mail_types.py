import pytest

from tapir.core.tapir_email_base import get_mail_types


class TapirEmailBase:
    pass


class MailTypeA(TapirEmailBase):
    enabled_by_default = True
    optional = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_type_a"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Type A"


class MailTypeB(TapirEmailBase):
    enabled_by_default = False
    optional = True

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_type_b"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Type B"


class MailTypeC(TapirEmailBase):
    enabled_by_default = True
    optional = True

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_type_c"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Type C"


# Tests
def test_get_mail_types_both():
    result = get_mail_types(
        enabled_by_default="both",
        optional="both",
        mail_classes=TapirEmailBase.__subclasses__(),
    )
    assert result == [MailTypeA, MailTypeB, MailTypeC]


def test_get_mail_types_enabled_by_default_true():
    result = get_mail_types(
        enabled_by_default=True,
        optional="both",
        mail_classes=TapirEmailBase.__subclasses__(),
    )
    assert result == [MailTypeA, MailTypeC]


def test_get_mail_types_enabled_by_default_false():
    result = get_mail_types(
        enabled_by_default=False,
        optional="both",
        mail_classes=TapirEmailBase.__subclasses__(),
    )
    assert result == [MailTypeB]


def test_get_mail_types_optional_true():
    result = get_mail_types(
        enabled_by_default="both",
        optional=True,
        mail_classes=TapirEmailBase.__subclasses__(),
    )
    assert result == [MailTypeB, MailTypeC]


def test_get_mail_types_optional_false():
    result = get_mail_types(
        enabled_by_default="both",
        optional=False,
        mail_classes=TapirEmailBase.__subclasses__(),
    )
    assert result == [MailTypeA]


# Führe die Tests aus
if __name__ == "__main__":
    pytest.main()
