from django.core.management import call_command

from tapir.utils.tests_utils import TapirFactoryTestBase


class TestGenerateTestDataCommand(TapirFactoryTestBase):
    def test_generateTestData_default_doesntFail(self):
        # We simply check that the command succeeds as it often fails after changes to models.
        # We don't check that the generated data is valid.
        call_command("generate_test_data", "--reset_all")
