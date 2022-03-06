import factory

from tapir.coop.models import ShareOwnership, ShareOwner


class ShareOwnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareOwnership

    start_date = factory.Faker("date")


class ShareOwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareOwner

    @factory.post_generation
    def nb_shares(self, create, extracted, **kwargs):
        if not create:
            return
        for _ in range(extracted or 1):
            ShareOwnershipFactory(owner=self)
