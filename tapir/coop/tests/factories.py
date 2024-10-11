import datetime

import factory
from dateutil.relativedelta import relativedelta
from faker import Faker

from tapir.accounts.models import TapirUser
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

fake = Faker()


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
        exclude = "pay_out_day"

    share_owner = factory.SubFactory(ShareOwnerFactory)
    cancellation_reason = factory.Faker("sentence")
    cancellation_date = factory.Faker("date_object")
    resignation_type = factory.Faker(
        "random_element",
        elements=[x[0] for x in MembershipResignation.ResignationType.choices],
    )
    transferring_shares_to = factory.LazyAttribute(
        lambda resignation: (
            ShareOwnerFactory.create()
            if resignation.resignation_type
            == MembershipResignation.ResignationType.TRANSFER
            else None
        )
    )
    paid_out = factory.LazyAttribute(
        lambda resignation: (
            fake.pybool()
            if resignation.resignation_type
            == MembershipResignation.ResignationType.BUY_BACK
            else False
        )
    )
    pay_out_day = factory.LazyAttribute(
        lambda resignation: (
            resignation.cancellation_date + relativedelta(day=31, month=12, years=3)
            if resignation.resignation_type
            == MembershipResignation.ResignationType.BUY_BACK
            else resignation.cancellation_date
        )
    )


class PurchaseBasketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseBasket

    cashier = 1
    purchase_counter = 1
    first_net_amount = 0
    second_net_amount = 0
    discount = 0


class GeneralAccountFactory(UserDataFactory):
    class Meta:
        model = TapirUser

    ATTRIBUTES = [
        "username",
        "first_name",
        "last_name",
        "usage_name",
        "pronouns",
        "email",
        "phone_number",
    ]

    username = factory.LazyAttribute(
        lambda o: f"{o.usage_name if o.usage_name else o.first_name}.{o.last_name}"
    )
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    usage_name = factory.Faker("first_name")
    pronouns = factory.Iterator(["he/him", "she/her", "they/them"])
    email = factory.Faker("email")
    phone_number = factory.LazyAttribute(lambda _: fake.phone_number())
