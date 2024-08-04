import datetime
import factory
import random

from tapir.accounts.tests.factories.user_data_factory import UserDataFactory
from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.models import (
    ShareOwnership,
    ShareOwner,
    DraftUser,
    MembershipPause,
    MembershipResignation,
)
from tapir.statistics.models import PurchaseBasket


class ShareOwnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareOwnership

    start_date = factory.Faker("date_object")
    amount_paid = factory.Faker("pydecimal", min_value=0, max_value=COOP_SHARE_PRICE)


class ShareOwnerFactory(UserDataFactory):
    class Meta:
        model = ShareOwner
        skip_postgeneration_save = True

    ATTRIBUTES = UserDataFactory.ATTRIBUTES + ["is_investing"]

    is_investing = factory.Faker("pybool")

    @factory.post_generation
    def nb_shares(self, create, nb_shares=None, **kwargs):
        if not create:
            return
        for _ in range(nb_shares if nb_shares is not None else 1):
            ShareOwnershipFactory.create(share_owner=self)


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


class MembershipPauseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MembershipPause
        exclude = "pause_duration"

    start_date = factory.Faker("date_object")
    pause_duration = factory.Faker("pyint", max_value=1000)
    end_date = factory.LazyAttribute(
        lambda pause: pause.start_date + datetime.timedelta(days=pause.pause_duration)
    )
    description = factory.Faker("bs")
    share_owner = factory.SubFactory(ShareOwnerFactory)


class MembershipResignationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MembershipResignation

    share_owner = factory.SubFactory(ShareOwnerFactory)
    cancellation_reason = factory.Faker("sentence")
    transferring_shares_to = factory.SubFactory(ShareOwnerFactory)
    resignation_type = factory.random.reseed_random(
        MembershipResignation.ResignationType
    )
    paid_out = factory.Faker("pybool")


class PurchaseBasketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseBasket

    cashier = 1
    purchase_counter = 1
    first_net_amount = 0
    second_net_amount = 0
    discount = 0
