from django.contrib.admin.widgets import AdminDateWidget
from django import forms

from tapir.coop.models import ShareOwnership


class CoopShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = (
            "start_date",
            "end_date",
        )

    start_date = forms.DateField(widget=AdminDateWidget())
    end_date = forms.DateField(widget=AdminDateWidget(), required=False)
