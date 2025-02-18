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
