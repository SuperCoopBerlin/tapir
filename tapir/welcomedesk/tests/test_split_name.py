from tapir.welcomedesk.serializers import split_name
from faker import Faker
import pytest

fake = Faker()


@pytest.mark.parametrize(
    "full_name,expected_first,expected_last",
    [
        ("", "", ""),
        ("John", "John", ""),
        ("John Doe", "John", "Doe"),
        ("Jean Paul Sartre", "Jean Paul", "Sartre"),
        ("Annegret Kramp-Karrenbauer", "Annegret", "Kramp-Karrenbauer"),
        ("Marie-Louise von Franz", "Marie-Louise", "von Franz"),
    ],
)
def test_split_name_manual(full_name, expected_first, expected_last):
    assert split_name(full_name) == (expected_first, expected_last)


def test_split_name_faker_random():
    """Weitere Tests mit Faker für zufällige Namen"""
    for _ in range(50):
        name = fake.name()
        first, last = split_name(name)

        # Invariante: Erste + Letzte sollte wieder den Namen ergeben
        if first and last:
            assert f"{first} {last}" == name.strip()
        elif first:
            assert first == name.strip()
