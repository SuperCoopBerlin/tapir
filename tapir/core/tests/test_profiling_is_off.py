from django.test import TestCase

from tapir import settings


class TestProfilingIsOff(TestCase):
    def test_profiling_is_off(self):
        self.assertFalse(
            settings.ENABLE_SILK_PROFILING,
            "Profiling should not be enabled in production or in the master branch",
        )
