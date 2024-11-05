from http import HTTPStatus
from unittest.mock import patch, Mock

from rest_framework.reverse import reverse

from tapir.utils.tests_utils import TapirFactoryTestBase
from tapir.welcomedesk.services.welcome_desk_reasons_cannot_shop_service import (
    WelcomeDeskReasonsCannotShopService,
)
from tapir.welcomedesk.services.welcome_desk_warnings_service import (
    WelcomeDeskWarningsService,
)


class TestWelcomeDeskAPI(TapirFactoryTestBase):
    def test_searchMemberForWelcomeDeskView_normalMember_accessDenied(self):
        tapir_user = self.login_as_normal_user()

        response = self.client.get(self.build_url(tapir_user.first_name))

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    @patch.object(WelcomeDeskWarningsService, "build_warnings")
    @patch.object(
        WelcomeDeskReasonsCannotShopService, "build_reasons_why_this_member_cannot_shop"
    )
    def test_searchMemberForWelcomeDeskView_default_callsServices(
        self,
        mock_build_reasons_why_this_member_cannot_shop: Mock,
        mock_build_warnings: Mock,
    ):
        tapir_user = self.login_as_member_office_user()
        mock_build_warnings.return_value = []
        mock_build_reasons_why_this_member_cannot_shop.return_value = []

        response = self.client.get(self.build_url(tapir_user.first_name))
        self.assertEqual(HTTPStatus.OK, response.status_code)

        mock_build_warnings.assert_called_once()
        self.assertEqual(
            tapir_user.share_owner, mock_build_warnings.call_args.kwargs["share_owner"]
        )

        mock_build_reasons_why_this_member_cannot_shop.assert_called_once()
        self.assertEqual(
            tapir_user.share_owner,
            mock_build_reasons_why_this_member_cannot_shop.call_args.kwargs[
                "share_owner"
            ],
        )

    def build_url(self, search_input):
        return reverse("welcomedesk:search") + f"?search_input={search_input}"
