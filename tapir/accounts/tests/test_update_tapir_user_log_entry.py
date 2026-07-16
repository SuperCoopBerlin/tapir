from tapir.accounts.models import UpdateTapirUserLogEntry
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.log.util import freeze_for_log
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestUpdateTapirUserLogEntry(TapirFactoryTestBase):
    def test_hstore_values_round_trip_as_dict_and_render(self):
        tapir_user = TapirUserFactory.create()

        UpdateTapirUserLogEntry().populate(
            actor=tapir_user,
            tapir_user=tapir_user,
            old_frozen={"phone_number": "before"},
            new_frozen={"phone_number": "after"},
        ).save()

        log_entry = UpdateTapirUserLogEntry.objects.get()

        self.assertIsInstance(log_entry.old_values, dict)
        self.assertIsInstance(log_entry.new_values, dict)
        self.assertEqual({"phone_number": "before"}, log_entry.old_values)
        self.assertEqual({"phone_number": "after"}, log_entry.new_values)
        self.assertEqual(
            [("phone_number", "before", "after")],
            log_entry.get_context_data()["changes"],
        )
        self.assertIn(
            "<strong>phone_number</strong>: before → after",
            log_entry.render(),
        )

    def test_freeze_for_log_excludes_password(self):
        tapir_user = TapirUserFactory.create()

        frozen = freeze_for_log(tapir_user)

        self.assertNotIn("password", frozen)
