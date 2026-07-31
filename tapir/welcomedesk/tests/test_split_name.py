from tapir.welcomedesk.serializers import split_name
import pytest


@pytest.mark.parametrize(
    "full_name,expected_first,expected_last",
    [
        ("", "", ""),
        ("John", "John", ""),
        ("John Doe", "John", "Doe"),
        ("Jean Paul Sartre", "Jean Paul", "Sartre"),
        ("Annegret Kramp-Karrenbauer", "Annegret", "Kramp-Karrenbauer"),
        ("Marie-Louise von Franz", "Marie-Louise", "von Franz"),
        ("Pellegrino van Dijk", "Pellegrino", "van Dijk"),
        (" Giacinto De Sousa", "Giacinto", "De Sousa"),
        ("Alyssa van der Noot", "Alyssa", "van der Noot"),
        ("Anton Berta; Caesar Emil", "Anton Berta; Caesar", "Emil"),
    ],
)
def test_split_name_manual(full_name, expected_first, expected_last):
    assert split_name(full_name) == (expected_first, expected_last)
