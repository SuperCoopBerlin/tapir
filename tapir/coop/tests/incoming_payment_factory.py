import factory

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.models import IncomingPayment
from tapir.coop.tests.factories import ShareOwnerFactory


class IncomingPaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncomingPayment

    paying_member = factory.SubFactory(ShareOwnerFactory)
    credited_member = factory.SubFactory(ShareOwnerFactory)
    amount = factory.Faker("pyint", min_value=10, max_value=1000)
    creation_date = factory.Faker("date_object")
    payment_date = factory.Faker("date_object")
    comment = factory.Faker("text")
    created_by = factory.SubFactory(TapirUserFactory)
