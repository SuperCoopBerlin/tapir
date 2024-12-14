import datetime
from unittest.mock import patch, Mock

from django.test import RequestFactory

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.statistics.models import FancyGraphCache
from tapir.statistics.views.fancy_graph.base_view import DatapointView
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class DummyDatapointView(DatapointView):
    VALUES = {
        datetime.date(year=2023, month=4, day=5): 10,
        datetime.date(year=2023, month=4, day=1): 8,
        datetime.date(year=2023, month=3, day=1): 5,
    }

    def calculate_datapoint(self, reference_time: datetime.datetime) -> int:
        return self.VALUES[reference_time.date()]


class TestDatapointView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)

    @patch.object(DummyDatapointView, "calculate_datapoint")
    def test_getDatapoint_noCache_callsCalculate(self, mock_calculate_datapoint: Mock):
        date = self.NOW - datetime.timedelta(days=5)
        mock_calculate_datapoint.return_value = 2

        result = DummyDatapointView().get_datapoint(date)

        mock_calculate_datapoint.assert_called_once_with(date)
        self.assertEqual(2, result)

    @patch.object(DummyDatapointView, "calculate_datapoint")
    def test_getDatapoint_hasCache_returnsCachedValue(
        self, mock_calculate_datapoint: Mock
    ):
        date = self.NOW - datetime.timedelta(days=5)
        mock_calculate_datapoint.return_value = 2
        view_name = f"{DummyDatapointView.__module__}.{DummyDatapointView.__name__}"
        FancyGraphCache.objects.create(view_name=view_name, date=date.date(), value=5)

        result = DummyDatapointView().get_datapoint(date)

        mock_calculate_datapoint.assert_not_called()
        self.assertEqual(5, result)

    @patch.object(DummyDatapointView, "calculate_datapoint")
    def test_getDatapoint_askingForTodaysData_doesntUseCachedValue(
        self, mock_calculate_datapoint: Mock
    ):
        mock_calculate_datapoint.return_value = 2
        view_name = f"{DummyDatapointView.__module__}.{DummyDatapointView.__name__}"
        FancyGraphCache.objects.create(
            view_name=view_name, date=self.NOW.date(), value=5
        )

        result = DummyDatapointView().get_datapoint(self.NOW)

        mock_calculate_datapoint.assert_called_once_with(self.NOW)
        self.assertEqual(2, result)

    def test_viewGet_notRelative_returnsDatapoint(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "", query_params={"relative": "false", "at_date": "2023-4-1"}
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DummyDatapointView.as_view()(request)

        self.assertEqual(8, response.data)

    def test_viewGet_relativeFromToday_returnsDiffFromTodayToStartOfMonth(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "", query_params={"relative": "true", "at_date": "2023-4-5"}
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DummyDatapointView.as_view()(request)

        self.assertEqual(2, response.data)

    def test_viewGet_relativeFromFirstOfMonth_returnsDiffFromLastMonth(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "", query_params={"relative": "true", "at_date": "2023-4-1"}
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DummyDatapointView.as_view()(request)

        self.assertEqual(3, response.data)
