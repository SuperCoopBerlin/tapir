from django.urls import reverse

from tapir.shifts.tests.factories import ShiftTemplateFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestMainStatisticsView(TapirFactoryTestBase):

    def test_default_pageRenders(self):
        # the stats page is complex and subject to changes.
        # We don't test it in detail but this at least makes sure that it doesn't fail.
        self.login_as_normal_user()
        ShiftTemplateFactory.create()
        self.client.get(reverse("statistics:main_statistics"))
