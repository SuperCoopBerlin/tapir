import factory


class UserDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True
        exclude = ("ATTRIBUTES",)

    ATTRIBUTES = [
        "first_name",
        "last_name",
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
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    street = factory.Faker("street_address")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    country = factory.Faker("country_code")
    preferred_language = factory.Iterator(["de", "en"])
    birthdate = factory.Faker("date_of_birth")
