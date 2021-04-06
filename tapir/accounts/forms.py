from django import forms

from tapir.accounts.models import TapirUser
from tapir.utils.forms import DateInput


class UserForm(forms.ModelForm):
    class Meta:
        model = TapirUser
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
        ]
        widgets = {
            "birthdate": DateInput(),
        }
