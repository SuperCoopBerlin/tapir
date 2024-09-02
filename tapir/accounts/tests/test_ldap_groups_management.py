from django.urls import reverse

from tapir.accounts.models import LdapGroup
from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.settings import GROUP_VORSTAND, GROUP_ACCOUNTING
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestLdapGroupsManagement(TapirFactoryTestBase):
    def test_vorstand_can_edit_groups(self):
        self.login_as_vorstand()
        member_to_add_to_accounting_team = TapirUserFactory.create(
            is_in_accounting_team=False
        )

        post_data = {"accounting": True}
        response = self.client.post(
            reverse(
                "accounts:edit_user_ldap_groups",
                args=[member_to_add_to_accounting_team.pk],
            ),
            post_data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        member_dn = member_to_add_to_accounting_team.get_ldap().build_dn()
        self.assertTrue(member_dn in LdapGroup.objects.get(cn=GROUP_ACCOUNTING).members)

    def test_employee_can_edit_groups(self):
        self.login_as_employee()
        member_to_add_to_accounting_team = TapirUserFactory.create(
            is_in_accounting_team=False
        )

        post_data = {"accounting": True}
        response = self.client.post(
            reverse(
                "accounts:edit_user_ldap_groups",
                args=[member_to_add_to_accounting_team.pk],
            ),
            post_data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        member_dn = member_to_add_to_accounting_team.get_ldap().build_dn()
        self.assertTrue(member_dn in LdapGroup.objects.get(cn=GROUP_ACCOUNTING).members)

    def test_employee_cannot_add_to_vorstand_group(self):
        self.login_as_employee()
        member_to_add_to_vorstand = TapirUserFactory.create(is_in_vorstand=False)

        post_data = {"vorstand": True}
        response = self.client.post(
            reverse(
                "accounts:edit_user_ldap_groups",
                args=[member_to_add_to_vorstand.pk],
            ),
            post_data,
            follow=True,
        )
        # Since the vorstand field is disabled, django will ignore our post data and set vorstand=true anyway.
        # That's why we don't get a 403 here
        self.assertEqual(200, response.status_code)

        member_dn = member_to_add_to_vorstand.get_ldap().build_dn()
        self.assertFalse(member_dn in LdapGroup.objects.get(cn=GROUP_VORSTAND).members)

    def test_employee_cannot_remove_from_vorstand_group(self):
        self.login_as_employee()
        member_to_remove_from_vorstand = TapirUserFactory.create(is_in_vorstand=True)

        post_data = {"vorstand": False}
        response = self.client.post(
            reverse(
                "accounts:edit_user_ldap_groups",
                args=[member_to_remove_from_vorstand.pk],
            ),
            post_data,
            follow=True,
        )
        # Since the vorstand field is disabled, django will ignore our post data and set vorstand=true anyway.
        # That's why we don't get a 403 here
        self.assertEqual(200, response.status_code)

        member_dn = member_to_remove_from_vorstand.get_ldap().build_dn()
        self.assertTrue(member_dn in LdapGroup.objects.get(cn=GROUP_VORSTAND).members)

    def test_member_office_cannot_edit_groups(self):
        self.login_as_member_office_user()
        member_to_add_to_accounting_team = TapirUserFactory.create(
            is_in_accounting_team=False
        )

        post_data = {"accounting": True}
        response = self.client.post(
            reverse(
                "accounts:edit_user_ldap_groups",
                args=[member_to_add_to_accounting_team.pk],
            ),
            post_data,
            follow=True,
        )
        self.assertEqual(403, response.status_code)

        member_dn = member_to_add_to_accounting_team.get_ldap().build_dn()
        self.assertFalse(
            member_dn in LdapGroup.get_group_members_dns(cn=GROUP_ACCOUNTING)
        )

    def test_vorstand_can_access_group_list_view(self):
        self.login_as_vorstand()

        response = self.client.get(reverse("accounts:ldap_group_list"))
        self.assertEqual(200, response.status_code)

    def test_employee_can_access_group_list_view(self):
        self.login_as_employee()

        response = self.client.get(reverse("accounts:ldap_group_list"))
        self.assertEqual(200, response.status_code)

    def test_member_office_cannot_access_group_list_view(self):
        self.login_as_member_office_user()

        response = self.client.get(reverse("accounts:ldap_group_list"))
        self.assertEqual(403, response.status_code)
