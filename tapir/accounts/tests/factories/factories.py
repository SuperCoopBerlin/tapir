import factory

from tapir import settings
from tapir.accounts.models import TapirUser, LdapGroup
from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.tests.factories import ShareOwnerFactory


class TapirUserFactory(UserDataFactory):
    class Meta:
        model = TapirUser
        skip_postgeneration_save = True

    username = factory.LazyAttribute(
        lambda o: f"{o.usage_name if o.usage_name else o.first_name}.{o.last_name}"
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
        group = LdapGroup.objects.filter(cn=group_cn).first()
        if not group:
            group = LdapGroup(cn=group_cn)
            group.members = []

        user_dn = tapir_user.get_ldap().build_dn()
        if is_member_of_group:
            group.members.append(user_dn)
            group.save()
            return

        if user_dn not in group.members:
            return

        # The current test setup uses the same LDAP server for all the tests, without resetting it in between tests,
        # so we have to make sure that this user has not been added to the member office by a previous test
        # or a previous run
        group.members.remove(user_dn)

        if group.members:
            group.save()
            return

        group.delete()

    @factory.post_generation
    def shift_capabilities(self, create, shift_capabilities, **kwargs):
        if not create:
            return

        self.shift_user_data.capabilities = shift_capabilities or []
        self.shift_user_data.save()
