from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.accounts.forms import TapirUserForm


class TestCoPurchaserDisabled(TapirFactoryTestBase):
    def test_TapirUserForm_hasCopurchaserDisabled_whenShareownerIsInvesting(self):
        tapir_user = TapirUserFactory.create()
        tapir_user.share_owner.is_investing = True
        tapir_user.share_owner.save()
        form = TapirUserForm(instance=tapir_user)
        self.assertTrue(form.fields["co_purchaser"].disabled)
