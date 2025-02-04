import datetime

from django.urls import reverse

from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.statistics.services.data_providers.base_data_provider import BaseDataProvider
from tapir.statistics.tests.tests_dataset_graph_point_view import DummyDataProvider
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestDatasetExportView(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)

    def setUp(self) -> None:
        super().setUp()
        self.NOW = mock_timezone_now(self, self.NOW)
        for i in range(10):
            ShareOwnerFactory.create(first_name=f"first_name_{i}")

        BaseDataProvider.register_data_provider(DummyDataProvider)

    def test_dataSetExportView_default_exportsRequiredColumns(self):
        self.login_as_member_office_user()

        response = self.client.get(
            reverse("statistics:export_dataset")
            + "?at_date=2023-03-01&export_columns=first_name&dataset=DummyDataProvider"
        )

        expected_result = [{"first_name": f"first_name_{i}"} for i in range(5)]
        self.assertEqual(expected_result, response.json())
