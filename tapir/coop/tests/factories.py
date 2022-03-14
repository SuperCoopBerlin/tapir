import factory

from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.models import ShareOwnership, ShareOwner, DraftUser


class ShareOwnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareOwnership

    start_date = factory.Faker("date")


class ShareOwnerFactory(UserDataFactory):
    class Meta:
        model = ShareOwner

    is_investing = factory.Faker("pybool")

    @factory.post_generation
    def nb_shares(self, create, nb_shares, **kwargs):
        if not create:
            return
        for _ in range(nb_shares or 1):
            ShareOwnershipFactory(owner=self)


class DraftUserFactory(UserDataFactory):
    class Meta:
        model = DraftUser

    num_shares = factory.Faker("pyint", min_value=1, max_value=20)
    is_investing = factory.Faker("pybool")
    paid_shares = factory.Faker("pybool")
