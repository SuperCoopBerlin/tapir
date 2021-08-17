from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.forms import ModelChoiceField
from django_select2.forms import Select2Widget

from tapir.accounts.models import TapirUser
from tapir.shifts.models import Shift, ShiftAttendanceTemplate


class ShiftCreateForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["name", "start_time", "end_time"]
        widgets = {
            "start_time": DateTimePickerInput().start_of("shift"),
            "end_time": DateTimePickerInput().end_of("shift"),
        }


class TapirUserChoiceField(ModelChoiceField):
    widget = Select2Widget()

    def __init__(self):
        # Super edgecase but filer out just to be sure
        # TODO(Leon Handreke): Filter out inactive when we can do it efficiently
        super().__init__(queryset=TapirUser.objects.filter(share_owner__isnull=False))

    def label_from_instance(self, obj: TapirUser):
        # Share Owner will always exist because we filter out all others above
        return "{} {} ({})".format(obj.first_name, obj.last_name, obj.share_owner.id)


class ShiftAttendanceTemplateForm(forms.ModelForm):
    user = TapirUserChoiceField()

    class Meta:
        model = ShiftAttendanceTemplate
        fields = ["user"]
