from tapir.core.tapir_email_base import get_all_emails, TapirEmailBase


def test_new_default_mail_is_recognized():
    class TestMail(TapirEmailBase):
        default = True

        @classmethod
        def get_unique_id(cls) -> str:
            return "tapir.test.TestMail"

    default_mails = get_all_emails(default=None)

    # print([mail.__name__ for mail in TapirEmailBase.__subclasses__()])
    assert "tapir.test.TestMail" in default_mails
