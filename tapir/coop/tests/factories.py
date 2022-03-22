import factory

from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.models import ShareOwnership, ShareOwner, DraftUser, COOP_SHARE_PRICE


class ShareOwnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareOwnership

    start_date = factory.Faker("date")
    amount_paid = factory.Faker("pydecimal", min_value=0, max_value=COOP_SHARE_PRICE)


class ShareOwnerFactory(UserDataFactory):
    class Meta:
        model = ShareOwner

    ATTRIBUTES = UserDataFactory.ATTRIBUTES + ["is_investing"]

    is_investing = factory.Faker("pybool")

    @factory.post_generation
    def nb_shares(self, create, nb_shares, **kwargs):
        if not create:
            return
        for _ in range(nb_shares or 1):
            ShareOwnershipFactory.create(owner=self)


class DraftUserFactory(UserDataFactory):
    class Meta:
        model = DraftUser

    ATTRIBUTES = UserDataFactory.ATTRIBUTES + [
        "num_shares",
        "is_investing",
        "paid_shares",
        "attended_welcome_session",
        "ratenzahlung",
        "paid_membership_fee",
        "signed_membership_agreement",
    ]

    num_shares = factory.Faker("pyint", min_value=1, max_value=20)
    is_investing = factory.Faker("pybool")
    paid_shares = factory.Faker("pybool")
    attended_welcome_session = factory.Faker("pybool")
    ratenzahlung = factory.Faker("pybool")
    paid_membership_fee = factory.Faker("pybool")
    signed_membership_agreement = factory.Faker("pybool")
