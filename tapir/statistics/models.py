# Create your models here.
from django.db import models

from tapir.accounts.models import TapirUser


class ProcessedPurchaseFiles(models.Model):
    MAX_FILE_NAME_LENGTH = 255

    file_name = models.CharField(max_length=255)
    processed_on = models.DateTimeField()


class ProcessedCreditFiles(models.Model):
    MAX_FILE_NAME_LENGTH = 255

    file_name = models.CharField(max_length=255)
    processed_on = models.DateTimeField()


class PurchaseBasket(models.Model):
    source_file = models.ForeignKey(ProcessedPurchaseFiles, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField()  # Datum & Zeit
    cashier = models.IntegerField()  # cKasse (column names from the CSV source file)
    purchase_counter = models.IntegerField()  # Bon
    tapir_user = models.ForeignKey(
        TapirUser, on_delete=models.SET_NULL, null=True
    )  # Kunde
    gross_amount = models.FloatField()  # VKBrutto_SUM
    first_net_amount = models.FloatField()  # VKNetto_SUM
    second_net_amount = models.FloatField()  # EKNetto_SUM
    discount = models.FloatField()  # Rabatt_SUM


class FancyGraphCache(models.Model):
    data_provider_name = models.CharField(max_length=500)
    date = models.DateField()
    value = models.IntegerField()

    def __str__(self):
        return f"{self.data_provider_name} - {self.date} - {self.value}"


class CreditAccount(models.Model):
    source_file = models.ForeignKey(ProcessedCreditFiles, on_delete=models.CASCADE)
    credit_date = models.DateTimeField()  # Datum & Zeit
    credit_amount = models.FloatField()  # Betrag
    credit_counter = models.IntegerField()  # Bon
    cashier = models.IntegerField()  # cKasse (column names from the CSV source file)
    info = models.CharField()  # Info (field from CSV source file)
    tapir_user = models.ForeignKey(
        TapirUser, on_delete=models.SET_NULL, null=True
    )  # Nutzer
