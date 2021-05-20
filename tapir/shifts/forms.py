from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.forms import DateTimeInput, SplitDateTimeWidget

from tapir.shifts.models import Shift


class ShiftCreateForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["name", "start_time", "end_time", "num_slots"]
        widgets = {
            "start_time": DateTimePickerInput().start_of("shift"),
            "end_time": DateTimePickerInput().end_of("shift"),
        }
