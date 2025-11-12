from tapir.accounts.forms import TapirUserForm
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestCoPurchaserMailFieldValidation(TapirFactoryTestBase):
    def test_tapirUserForm_coPurchaser1SetAndNoMailGiven_formIsValid(self):
        form = TapirUserForm(
            data={
                "co_purchaser": "John Doe",
                "co_purchaser_mail": "",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertTrue(form.is_valid())

    def test_tapirUserForm_coPurchaser1NotSetAndNoMailGiven_formIsValid(self):
        form = TapirUserForm(
            data={
                "co_purchaser": "",
                "co_purchaser_mail": "",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertTrue(form.is_valid())

    def test_tapirUserForm_coPurchaser1NotSetAndMailGiven_formIsInvalid(self):
        form = TapirUserForm(
            data={
                "co_purchaser": "",
                "co_purchaser_mail": "john.doe@example.com",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertFalse(form.is_valid())

    def test_tapirUserForm_coPurchaser2SetAndNoMailGiven_formIsValid(self):
        form = TapirUserForm(
            data={
                "co_purchaser_2": "John Doe",
                "co_purchaser_2_mail": "",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertTrue(form.is_valid())

    def test_tapirUserForm_coPurchaser2NotSetAndNoMailGiven_formIsValid(self):
        form = TapirUserForm(
            data={
                "co_purchaser_2": "",
                "co_purchaser_mail_2": "",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertTrue(form.is_valid())

    def test_tapirUserForm_coPurchaser2NotSetAndMailGiven_formIsInvalid(self):
        form = TapirUserForm(
            data={
                "co_purchaser_2": "",
                "co_purchaser_2_mail": "john.doe@example.com",
                "preferred_language": "de",
                "username": "john.doe",
            }
        )

        self.assertFalse(form.is_valid())
