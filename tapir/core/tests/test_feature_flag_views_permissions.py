import pytest
from django.conf import settings
from django.urls import reverse

from tapir.core.models import FeatureFlag
from tapir.settings import LOGIN_BACKEND_COOPS_PT
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestFeatureFlagViewsPermissions(TapirFactoryTestBase):
    FLAG_NAME = "test_flag_name"

    @pytest.mark.skipif(
        settings.ACTIVE_LOGIN_BACKEND == LOGIN_BACKEND_COOPS_PT,
        reason="The coops pt login backend doesn't differentiate between groups, all group members are admin",
    )
    def test_featureFlagList_memberOffice_cannotAccess(self):
        self.login_as_member_office_user()
        response = self.client.get(reverse("core:featureflag_list"))
        self.assertEqual(response.status_code, 403)

    def test_featureFlagList_vorstand_canAccess(self):
        self.login_as_vorstand()
        response = self.client.get(reverse("core:featureflag_list"))
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skipif(
        settings.ACTIVE_LOGIN_BACKEND == LOGIN_BACKEND_COOPS_PT,
        reason="The coops pt login backend doesn't differentiate between groups, all group members are admin",
    )
    def test_featureFlagUpdate_memberOffice_cannotAccess(self):
        feature_flag = FeatureFlag.objects.create(flag_name="TEST_FLAG")
        self.login_as_member_office_user()
        response = self.client.get(
            reverse("core:featureflag_update", args=[feature_flag.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_featureFlagUpdate_vorstand_canAccess(self):
        feature_flag = FeatureFlag.objects.create(flag_name="TEST_FLAG")
        self.login_as_vorstand()
        response = self.client.get(
            reverse("core:featureflag_update", args=[feature_flag.id])
        )
        self.assertEqual(response.status_code, 200)
