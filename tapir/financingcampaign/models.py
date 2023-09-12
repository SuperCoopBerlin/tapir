import datetime

from django.db import models

from tapir.utils.models import DurationModelMixin


class FinancingCampaign(DurationModelMixin, models.Model):
    name = models.CharField(blank=False, null=False, max_length=200)
    goal = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return f"{self.name} #{self.id}"


class FinancingSource(models.Model):
    name = models.CharField(blank=False, null=False, max_length=200)
    campaign = models.ForeignKey(
        to=FinancingCampaign, blank=False, null=False, on_delete=models.deletion.CASCADE
    )

    def __str__(self):
        return f"{self.campaign}: {self.name} #{self.id}"


class FinancingSourceDatapoint(models.Model):
    date = models.DateField(blank=False, null=False, default=datetime.date.today)
    source = models.ForeignKey(
        to=FinancingSource, blank=False, null=False, on_delete=models.deletion.CASCADE
    )
    value = models.FloatField(blank=False, null=False)

    def __str__(self):
        return f"{self.source}: {self.date} - {self.value}"
