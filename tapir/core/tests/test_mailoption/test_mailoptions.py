from tapir.core.mail_option import MailOption


class TestMailOptions:
    def test_optional_enabled(self):
        assert MailOption.OPTIONAL_ENABLED.is_optional() is True

    def test_optional_disabled(self):
        assert MailOption.OPTIONAL_DISABLED.is_optional() is True

    def test_mandatory(self):
        assert MailOption.MANDATORY.is_optional() is False
