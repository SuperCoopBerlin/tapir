from django.urls import reverse

from tapir.utils.tests_utils import TapirFactoryTestBase


class TestAvailableDatasetsView(TapirFactoryTestBase):

    def test_availableDatasetsView_default_alwaysReturnsTheSameColors(self):
        self.login_as_member_office_user()

        response = self.client.get(reverse("statistics:available_datasets"))
        colors_first_request = [dataset["color"] for dataset in response.json()]

        response = self.client.get(reverse("statistics:available_datasets"))
        colors_second_request = [dataset["color"] for dataset in response.json()]

        self.assertEqual(colors_first_request, colors_second_request)

    def test_availableDatasetsView_withColourblindnessParameter_returnsDifferentColorsAsWithoutColourblindness(
        self,
    ):
        self.login_as_member_office_user()

        response = self.client.get(reverse("statistics:available_datasets"))
        colors_without_colourblindness = [
            dataset["color"] for dataset in response.json()
        ]

        response = self.client.get(
            reverse("statistics:available_datasets") + "?colourblindness=Protanopia"
        )
        colors_with_colourblindness = [dataset["color"] for dataset in response.json()]

        self.assertNotEqual(colors_without_colourblindness, colors_with_colourblindness)
