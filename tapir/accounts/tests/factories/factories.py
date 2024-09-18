import factory

from tapir import settings
from tapir.accounts.models import TapirUser
from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.utils.shortcuts import set_group_membership


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
    def password(self: TapirUser, create, password, **kwargs):
        if not create:
            return
        self.set_password(password or self.username)

    @factory.post_generation
    def is_in_vorstand(self: TapirUser, create, is_in_vorstand, **kwargs):
        if not create:
            return

        set_group_membership([self], settings.GROUP_VORSTAND, is_in_vorstand)

    @factory.post_generation
    def is_in_member_office(self: TapirUser, create, is_in_member_office, **kwargs):
        if not create:
            return

        set_group_membership([self], settings.GROUP_MEMBER_OFFICE, is_in_member_office)

    @factory.post_generation
    def is_in_accounting_team(self: TapirUser, create, is_in_accounting_team, **kwargs):
        if not create:
            return

        set_group_membership([self], settings.GROUP_ACCOUNTING, is_in_accounting_team)

    @factory.post_generation
    def is_shift_manager(self: TapirUser, create, is_shift_manager, **kwargs):
        if not create:
            return

        set_group_membership([self], settings.GROUP_SHIFT_MANAGER, is_shift_manager)

    @factory.post_generation
    def is_employee(self: TapirUser, create, is_employee):
        if not create:
            return

        set_group_membership([self], settings.GROUP_EMPLOYEES, is_employee)

    @factory.post_generation
    def shift_capabilities(self: TapirUser, create, shift_capabilities, **kwargs):
        if not create:
            return

        self.shift_user_data.capabilities = shift_capabilities or []
        self.shift_user_data.save()
