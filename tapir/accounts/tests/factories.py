import factory

from tapir.accounts.models import TapirUser
from tapir.coop.tests.factories import ShareOwnerFactory


class TapirUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TapirUser

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.LazyAttribute(lambda o: f"{o.first_name}.{o.last_name}")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    street = factory.Faker("street_address")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    country = factory.Faker("country_code")
    preferred_language = factory.Iterator(["de", "en"])
    birthdate = factory.Faker("date_of_birth")

    share_owner = factory.RelatedFactory(
        ShareOwnerFactory,
        factory_related_name="user",
        nb_shares=factory.Faker("pyint", min_value=1, max_value=20),
    )

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or self.username)
