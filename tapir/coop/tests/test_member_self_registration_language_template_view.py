from http import HTTPStatus

from django.urls import reverse

from tapir.coop.config import feature_flag_self_registration_enabled
from tapir.core.models import FeatureFlag
from tapir.utils.tests_utils import (
    TapirEmailTestMixin,
    TapirFactoryTestBase,
)


class TestMemberSelfRegistrationLanguageTemplateView(
    TapirEmailTestMixin, TapirFactoryTestBase
):
    @classmethod
    def setUpTestData(cls) -> None:
        FeatureFlag.ensure_flag_exists(feature_flag_self_registration_enabled)

    def test_get_flagDisabled_returnsError(self):
        FeatureFlag.set_flag_value(feature_flag_self_registration_enabled, False)

        response = self.client.get(reverse("coop:member_self_registration_language"))

        self.assertStatusCode(response, HTTPStatus.FORBIDDEN)

    def test_get_flagEnabled_returns200(self):
        FeatureFlag.set_flag_value(feature_flag_self_registration_enabled, True)

        response = self.client.get(reverse("coop:member_self_registration_language"))

        self.assertStatusCode(response, HTTPStatus.OK)
