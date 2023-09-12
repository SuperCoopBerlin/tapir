from django import forms

from tapir.financingcampaign.models import (
    FinancingCampaign,
    FinancingSource,
    FinancingSourceDatapoint,
)
from tapir.utils.forms import DateInputTapir


class FinancingCampaignForm(forms.ModelForm):
    class Meta:
        model = FinancingCampaign
        fields = ["name", "goal", "start_date", "end_date"]
        widgets = {
            "start_date": DateInputTapir(),
            "end_date": DateInputTapir(),
        }


class FinancingSourceForm(forms.ModelForm):
    class Meta:
        model = FinancingSource
        fields = ["campaign", "name"]


class FinancingSourceDatapointForm(forms.ModelForm):
    class Meta:
        model = FinancingSourceDatapoint
        fields = ["source", "date", "value"]
        widgets = {
            "date": DateInputTapir(),
        }
