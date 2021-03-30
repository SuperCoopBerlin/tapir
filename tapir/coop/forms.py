from django.contrib.admin.widgets import AdminDateWidget
from django import forms

from tapir.coop.models import ShareOwnership, DraftUser


class CoopShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = (
            "start_date",
            "end_date",
        )

    start_date = forms.DateField(widget=AdminDateWidget())
    end_date = forms.DateField(widget=AdminDateWidget(), required=False)


class DateInput(forms.DateInput):
    input_type = "date"


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
