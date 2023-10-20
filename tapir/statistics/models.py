# Create your models here.
from django.db import models

from tapir.accounts.models import TapirUser


class ProcessedPurchaseFiles(models.Model):
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
