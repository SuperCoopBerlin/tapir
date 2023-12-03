import datetime

from django.urls import reverse

from tapir.coop.tests.factories import PurchaseBasketFactory
from tapir.statistics.models import ProcessedPurchaseFiles
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now


class TestBasketSumEvolutionData(TapirFactoryTestBase):
    NOW = datetime.datetime(year=2023, month=4, day=1, hour=12)

    def test_get_basket_sums_per_month(self):
        user = self.login_as_normal_user()
        mock_timezone_now(self, self.NOW)

        self.create_payment(
            date=datetime.date(year=2023, month=1, day=1),
            amount=10.00,
            source_file=self.getSourceFile(),
            user=user,
        )
        self.create_payment(
            date=datetime.date(year=2023, month=4, day=1),
            amount=20.00,
            source_file=self.getSourceFile(),
            user=user,
        )
        self.create_payment(
            date=datetime.date(year=2023, month=4, day=1),
            amount=10.50,
            source_file=self.getSourceFile(),
            user=user,
        )

        response = self.client.get(
            reverse("statistics:basket_sum_evolution_json", kwargs={"pk": user.pk}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(  # assert months
            response.json()["data"]["labels"],
            ["2023-01", "2023-02", "2023-03", "2023-04"],
        )
        self.assertEqual(  # assert values
            response.json()["data"]["datasets"][0]["data"], [10.0, 0, 0, 30.5]
        )

    def test_requires_permissions(self):
        user = self.login_as_normal_user()

        another_user_pk = user.pk + 1
        response = self.client.get(
            reverse(
                "statistics:basket_sum_evolution_json", kwargs={"pk": another_user_pk}
            ),
        )
        self.assertEqual(response.status_code, 403)

    @staticmethod
    def create_payment(date, amount, source_file, user):
        PurchaseBasketFactory.create(
            purchase_date=date,
            gross_amount=amount,
            source_file=source_file,
            tapir_user=user,
        )

    @staticmethod
    def getSourceFile():
        return ProcessedPurchaseFiles.objects.create(
            file_name=f"test_basket_file",
            processed_on=datetime.datetime.now(),
        )
