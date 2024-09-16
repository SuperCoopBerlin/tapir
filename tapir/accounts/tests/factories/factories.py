import factory
import ldap
from icecream import ic
from ldap.ldapobject import LDAPObject

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.shortcuts import build_ldap_group_dn


class TapirUserFactory(UserDataFactory):
    class Meta:
        model = TapirUser
        skip_postgeneration_save = True

    username = factory.LazyAttribute(
        lambda o: f"{o.usage_name if o.usage_name else o.first_name}.{o.last_name}".lower()
    )

    share_owner = factory.RelatedFactory(
        ShareOwnerFactory,
        factory_related_name="user",
        nb_shares=factory.Faker("pyint", min_value=1, max_value=20),
    )

    allows_purchase_tracking = factory.Faker("pybool")

    @factory.post_generation
    def password(self, create, password, **kwargs):
        if not create:
            return
        self.set_password(password or self.username)

    @factory.post_generation
    def is_in_vorstand(self, create, is_in_vorstand, **kwargs):
        if not create:
            return

        TapirUserFactory._set_group_membership(
            self, settings.GROUP_VORSTAND, is_in_vorstand
        )

    @factory.post_generation
    def is_in_member_office(self, create, is_in_member_office, **kwargs):
        if not create:
            return

        TapirUserFactory._set_group_membership(
            self, settings.GROUP_MEMBER_OFFICE, is_in_member_office
        )

    @factory.post_generation
    def is_in_accounting_team(self, create, is_in_accounting_team, **kwargs):
        if not create:
            return

        TapirUserFactory._set_group_membership(
            self, settings.GROUP_ACCOUNTING, is_in_accounting_team
        )

    @factory.post_generation
    def is_shift_manager(self, create, is_shift_manager, **kwargs):
        if not create:
            return

        TapirUserFactory._set_group_membership(
            self, settings.GROUP_SHIFT_MANAGER, is_shift_manager
        )

    @factory.post_generation
    def is_employee(self, create, is_employee, **kwargs):
        if not create:
            return

        TapirUserFactory._set_group_membership(
            self, settings.GROUP_EMPLOYEES, is_employee
        )

    @staticmethod
    def _set_group_membership(
        tapir_user: TapirUser, group_cn: str, is_member_of_group: bool
    ):
        ic(tapir_user.id)
        connection: LDAPObject = tapir_user.get_ldap_user().connection
        group_dn = build_ldap_group_dn(group_cn)
        user_dn = tapir_user.build_ldap_dn()
        connection.modify_s(
            group_dn,
            [
                (
                    ldap.MOD_ADD if is_member_of_group else ldap.MOD_DELETE,
                    "member",
                    [user_dn],
                )
            ],
        )

    @factory.post_generation
    def shift_capabilities(self, create, shift_capabilities, **kwargs):
        if not create:
            return

        self.shift_user_data.capabilities = shift_capabilities or []
        self.shift_user_data.save()
