from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from tapir.shifts.models import CapabilityTranslation
from tapir.shifts.tests.factories import CapabilityFactory, CapabilityTranslationFactory


class CapabilityTranslationUniquenessTest(TestCase):
    def setUp(self):
        self.capability = CapabilityFactory()
        self.other_capability = CapabilityFactory()

    def test_capabilityTranslation_duplicateLanguageForSameCapability_throwsIntegrityError(
        self,
    ):
        CapabilityTranslationFactory.create(
            capability=self.capability,
            language="de",
            name="Erste Hilfe",
            description="Beschreibung",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CapabilityTranslationFactory.create(
                capability=self.capability,
                language="de",
                name="Doppelt",
                description="Beschreibung",
            )

    def test_capabilityTranslation_sameLanguageForDifferentCapabilities_isAllowed(self):
        before = CapabilityTranslation.objects.filter(
            language="de"
        ).count()  # take credit of capabilies from migration
        CapabilityTranslationFactory.create(
            capability=self.capability,
            language="de",
            name="A",
            description="A",
        )
        CapabilityTranslationFactory.create(
            capability=self.other_capability,
            language="de",
            name="B",
            description="B",
        )
        self.assertEqual(
            CapabilityTranslation.objects.filter(language="de").count(), before + 2
        )

    def test_capabilityTranslation_FullClean_reportsduplicate(self):
        CapabilityTranslationFactory.create(
            capability=self.capability,
            language="de",
            name="A",
            description="A",
        )
        duplicate = CapabilityTranslationFactory.build(
            capability=self.capability,
            language="de",
            name="B",
            description="B",
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
