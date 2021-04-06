from django.contrib.admin.widgets import AdminDateWidget
from django import forms

from tapir.coop.models import ShareOwnership, DraftUser
from tapir.utils.forms import DateInput


class CoopShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = (
            "start_date",
            "end_date",
        )

    start_date = forms.DateField(widget=AdminDateWidget())
    end_date = forms.DateField(widget=AdminDateWidget(), required=False)


class DraftUserForm(forms.ModelForm):
    class Meta:
        model = DraftUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "num_shares",
            "attended_welcome_session",
        ]
        widgets = {
            "birthdate": DateInput(),
        }
