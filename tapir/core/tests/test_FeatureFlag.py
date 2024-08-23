from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from tapir.core.models import FeatureFlag


class TestFeatureFlag(SimpleTestCase):
    FLAG_NAME = "test_flag_name"

    @patch.object(FeatureFlag, "objects")
    def test_getFlagValue_flagNotDefined_createsFlagAndReturnsFalse(
        self, mock_feature_flag_objects: Mock
    ):
        mock_feature_flag = Mock()
        mock_feature_flag.flag_value = False
        mock_feature_flag_objects.get_or_create.return_value = (mock_feature_flag, True)
        self.assertFalse(FeatureFlag.get_flag_value(self.FLAG_NAME))
        mock_feature_flag_objects.get_or_create.assert_called_once_with(
            flag_name=self.FLAG_NAME, defaults={"flag_value": False}
        )

    @patch.object(FeatureFlag, "objects")
    def test_getFlagValue_flagDefined_returnsFlagValue(
        self, mock_feature_flag_objects: Mock
    ):
        feature_flag_mock = Mock()
        flag_value = Mock()
        feature_flag_mock.flag_value = flag_value
        mock_feature_flag_objects.get_or_create.return_value = (
            feature_flag_mock,
            False,
        )
        self.assertIs(flag_value, FeatureFlag.get_flag_value(self.FLAG_NAME))
        mock_feature_flag_objects.get_or_create.assert_called_once_with(
            flag_name=self.FLAG_NAME, defaults={"flag_value": False}
        )

    @patch.object(FeatureFlag, "objects")
    def test_setFlagValue_default(self, mock_feature_flag_objects: Mock):
        flag_value = False
        mock_feature_flag = Mock()
        mock_feature_flag_objects.get.return_value = mock_feature_flag
        FeatureFlag.set_flag_value(self.FLAG_NAME, flag_value)
        mock_feature_flag_objects.get.assert_called_once_with(flag_name=self.FLAG_NAME)
        self.assertEqual(flag_value, mock_feature_flag.flag_value)
        mock_feature_flag.save.assert_called_once_with()

    @patch.object(FeatureFlag, "objects")
    def test_ensureFeatureFlagExists_flagExists_noFlagCreated(
        self, mock_feature_flag_objects: Mock
    ):
        mock_feature_flag_objects.filter.return_value.exists.return_value = True
        FeatureFlag.ensure_flag_exists(flag_name=self.FLAG_NAME)
        mock_feature_flag_objects.filter.assert_called_once_with(
            flag_name=self.FLAG_NAME
        )
        mock_feature_flag_objects.filter.return_value.exists.assert_called_once_with()
        mock_feature_flag_objects.create.assert_not_called()

    @patch.object(FeatureFlag, "objects")
    def test_ensureFeatureFlagExists_flagDoesNotExist_flagCreated(
        self, mock_feature_flag_objects: Mock
    ):
        mock_feature_flag_objects.filter.return_value.exists.return_value = False
        FeatureFlag.ensure_flag_exists(flag_name=self.FLAG_NAME)
        mock_feature_flag_objects.filter.assert_called_once_with(
            flag_name=self.FLAG_NAME
        )
        mock_feature_flag_objects.filter.return_value.exists.assert_called_once_with()
        mock_feature_flag_objects.create.assert_called_once_with(
            flag_name=self.FLAG_NAME
        )
