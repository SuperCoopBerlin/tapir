import datetime
from unittest.mock import patch, Mock

from django.db.models import QuerySet
from django.test import RequestFactory

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.models import FancyGraphCache
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider
from tapir.statistics.views.dataset_graph_point_view import DatasetGraphPointView
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class DummyDataProvider(BaseDataProvider):
    VALUES = {
        datetime.date(year=2023, month=4, day=5): 10,
        datetime.date(year=2023, month=4, day=1): 8,
        datetime.date(year=2023, month=3, day=1): 5,
    }

    @classmethod
    def get_display_name(cls):
        return "Test display name"

    @classmethod
    def get_description(cls):
        return "Test description"

    @classmethod
    def get_queryset(cls, reference_time: datetime.datetime) -> QuerySet[ShareOwner]:
        if reference_time.date() == datetime.date(year=2023, month=4, day=1):
            return ShareOwner.objects.filter(
                id__in=ShareOwner.objects.all()[:8].values_list("id", flat=True)
            )
        if reference_time.date() == datetime.date(year=2023, month=3, day=1):
            return ShareOwner.objects.filter(
                id__in=ShareOwner.objects.all()[:5].values_list("id", flat=True)
            )
        return ShareOwner.objects.filter(
            id__in=ShareOwner.objects.all()[:10].values_list("id", flat=True)
        )


class TestDatasetGraphPointView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)
        for _ in range(10):
            ShareOwnerFactory.create()

        BaseDataProvider.register_data_provider(DummyDataProvider)

    @patch.object(DatasetGraphPointView, "calculate_datapoint")
    def test_getDatapoint_noCache_callsCalculate(self, mock_calculate_datapoint: Mock):
        date = self.NOW - datetime.timedelta(days=5)
        mock_calculate_datapoint.return_value = 2

        result = DatasetGraphPointView().get_datapoint(DummyDataProvider, date)

        mock_calculate_datapoint.assert_called_once_with(DummyDataProvider, date)
        self.assertEqual(2, result)

    @patch.object(DatasetGraphPointView, "calculate_datapoint")
    def test_getDatapoint_hasCache_returnsCachedValue(
        self, mock_calculate_datapoint: Mock
    ):
        date = self.NOW - datetime.timedelta(days=5)
        mock_calculate_datapoint.return_value = 2
        view_name = f"{DummyDataProvider.__module__}.{DummyDataProvider.__name__}"
        FancyGraphCache.objects.create(
            data_provider_name=view_name, date=date.date(), value=5
        )

        result = DatasetGraphPointView().get_datapoint(DummyDataProvider, date)

        mock_calculate_datapoint.assert_not_called()
        self.assertEqual(5, result)

    @patch.object(DatasetGraphPointView, "calculate_datapoint")
    def test_getDatapoint_askingForTodaysData_doesntUseCachedValue(
        self, mock_calculate_datapoint: Mock
    ):
        mock_calculate_datapoint.return_value = 2
        view_name = f"{DummyDataProvider.__module__}.{DummyDataProvider.__name__}"
        FancyGraphCache.objects.create(
            data_provider_name=view_name, date=self.NOW.date(), value=5
        )

        result = DatasetGraphPointView().get_datapoint(DummyDataProvider, self.NOW)

        mock_calculate_datapoint.assert_called_once_with(DummyDataProvider, self.NOW)
        self.assertEqual(2, result)

    def test_viewGet_notRelative_returnsDatapoint(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "",
            query_params={
                "relative": "false",
                "at_date": "2023-4-1",
                "dataset": "DummyDataProvider",
            },
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DatasetGraphPointView.as_view()(request)

        self.assertEqual(8, response.data)

    def test_viewGet_relativeFromToday_returnsDiffFromTodayToStartOfMonth(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "",
            query_params={
                "relative": "true",
                "at_date": "2023-4-5",
                "dataset": "DummyDataProvider",
            },
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DatasetGraphPointView.as_view()(request)

        self.assertEqual(2, response.data)

    def test_viewGet_relativeFromFirstOfMonth_returnsDiffFromLastMonth(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "",
            query_params={
                "relative": "true",
                "at_date": "2023-4-1",
                "dataset": "DummyDataProvider",
            },
        )
        request.user = TapirUserFactory.create(is_in_member_office=True)

        response = DatasetGraphPointView.as_view()(request)

        self.assertEqual(3, response.data)
