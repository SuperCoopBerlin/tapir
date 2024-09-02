import unittest

from django.test import SimpleTestCase

from tapir.shifts.models import ShiftNames


class ShiftNamesTestCase(SimpleTestCase):
    def test_get_names_for_index(self):
        self.assertEqual("A", ShiftNames.get_name(0))
        self.assertEqual("B", ShiftNames.get_name(1))
        self.assertEqual("C", ShiftNames.get_name(2))
        self.assertEqual("D", ShiftNames.get_name(3))

    def test_get_indexes_for_name(self):
        self.assertEqual(0, ShiftNames.get_index("A"))
        self.assertEqual(1, ShiftNames.get_index("B"))
        self.assertEqual(2, ShiftNames.get_index("C"))
        self.assertEqual(3, ShiftNames.get_index("D"))

    def test_unknown_names_cause_index_None(self):
        self.assertIsNone(ShiftNames.get_name(24))

    def test_unknown_index_cause_name_None(self):
        self.assertIsNone(ShiftNames.get_index("foobar"))


if __name__ == "__main__":
    unittest.main()
