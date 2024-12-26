import pytest

from tapir.core.tapir_email_base import get_mail_types


class EmailBaseTest:
    pass


class MailTypeA(EmailBaseTest):
    enabled_by_default = True
    optional = False

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_type_a"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Type A"


class MailTypeB(EmailBaseTest):
    enabled_by_default = False
    optional = True

    @classmethod
    def get_unique_id(cls) -> str:
        return "mail_type_b"

    @classmethod
    def get_name(cls) -> str:
        return "Mail Type B"


class MailTypeC(EmailBaseTest):
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
        mail_classes=EmailBaseTest.__subclasses__(),
    )
    assert result == [
        ("mail_type_a", "Mail Type A"),
        ("mail_type_b", "Mail Type B"),
        ("mail_type_c", "Mail Type C"),
    ]


def test_get_mail_types_enabled_by_default_true():
    result = get_mail_types(
        enabled_by_default=True,
        optional="both",
        mail_classes=EmailBaseTest.__subclasses__(),
    )
    assert result == [
        ("mail_type_a", "Mail Type A"),
        ("mail_type_c", "Mail Type C"),
    ]


def test_get_mail_types_enabled_by_default_false():
    result = get_mail_types(
        enabled_by_default=False,
        optional="both",
        mail_classes=EmailBaseTest.__subclasses__(),
    )
    assert result == [
        ("mail_type_b", "Mail Type B"),
    ]


def test_get_mail_types_optional_true():
    result = get_mail_types(
        enabled_by_default="both",
        optional=True,
        mail_classes=EmailBaseTest.__subclasses__(),
    )
    assert result == [
        ("mail_type_b", "Mail Type B"),
        ("mail_type_c", "Mail Type C"),
    ]


def test_get_mail_types_optional_false():
    result = get_mail_types(
        enabled_by_default="both",
        optional=False,
        mail_classes=EmailBaseTest.__subclasses__(),
    )
    assert result == [
        ("mail_type_a", "Mail Type A"),
    ]


# Führe die Tests aus
if __name__ == "__main__":
    pytest.main()
