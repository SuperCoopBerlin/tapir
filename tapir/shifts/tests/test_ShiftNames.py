import unittest

from tapir.shifts.models import ShiftNames


class ShiftNamesTestCase(unittest.TestCase):
    def test_get_names_for_index(self):
        self.assertEquals("A", ShiftNames.get_name(0))
        self.assertEquals("B", ShiftNames.get_name(1))
        self.assertEquals("C", ShiftNames.get_name(2))
        self.assertEquals("D", ShiftNames.get_name(3))

    def test_get_indexes_for_name(self):
        self.assertEquals(0, ShiftNames.get_index("A"))
        self.assertEquals(1, ShiftNames.get_index("B"))
        self.assertEquals(2, ShiftNames.get_index("C"))
        self.assertEquals(3, ShiftNames.get_index("D"))

    def test_unknown_names_cause_index_None(self):
        self.assertIsNone(ShiftNames.get_name(24))

    def test_unknown_index_cause_name_None(self):
        self.assertIsNone(ShiftNames.get_index("foobar"))


if __name__ == "__main__":
    unittest.main()
