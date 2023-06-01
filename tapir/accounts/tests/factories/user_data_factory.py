import factory
import phonenumbers
from faker import Faker
from faker.providers.phone_number.de_DE import Provider


class CustomPhoneProvider(Provider):
    # From https://stackoverflow.com/a/57875941
    # Faker sometimes generates invalid phone numbers, like (182)722-5289x4545.
    # Even with factory.Faker("phone_number", locale="de"), it sometimes generates numbers that are too short.
    def phone_number(self):
        tries = 0
        while tries < 10:
            phone_number = self.numerify(self.random_element(self.formats))
            try:
                parsed_number = phonenumbers.parse(phone_number, "DE")
            except phonenumbers.phonenumberutil.NumberParseException:
                continue
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )
            tries += 1
        return "+4917612345678"


fake = Faker()
fake.add_provider(CustomPhoneProvider)


class UserDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True
        exclude = ("ATTRIBUTES",)

    ATTRIBUTES = [
        "first_name",
        "last_name",
        "usage_name",
        "pronouns",
        "email",
        "phone_number",
        "birthdate",
        "street",
        "street_2",
        "postcode",
        "city",
        "country",
        "preferred_language",
    ]

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    usage_name = factory.Faker("first_name")
    pronouns = factory.Iterator(["he/him", "she/her", "they/them"])
    email = factory.Faker("email")
    phone_number = factory.LazyAttribute(lambda _: fake.phone_number())
    street = factory.Faker("street_address")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    country = factory.Faker("country_code")
    preferred_language = factory.Iterator(["de", "en"])
    birthdate = factory.Faker("date_of_birth")
