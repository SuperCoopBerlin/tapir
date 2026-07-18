from django.urls import reverse

from tapir import settings
from tapir.utils.tests_utils import PermissionTestMixin, TapirFactoryTestBase


class TestCoopManagement(PermissionTestMixin, TapirFactoryTestBase):

    def get_allowed_groups(self):
        return [
            settings.GROUP_VORSTAND,
        ]

    def do_request(self):
        return self.client.post(
            reverse("coop:coop_management"),
            data={"street": "221B Baker Street"},
            follow=True,
        )
