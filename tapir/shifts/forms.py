from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, CheckboxSelectMultiple
from django.utils.translation import gettext as _
from django_select2.forms import Select2Widget

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    Shift,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftUserData,
    SHIFT_USER_CAPABILITY_CHOICES,
    ShiftSlotTemplate,
)


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

    def __init__(self, *args, **kwargs):
        self.slot_template = ShiftSlotTemplate.objects.get(
            pk=kwargs.pop("slot_template_pk", None)
        )
        super().__init__(*args, **kwargs)

    def clean_user(self):
        user = self.cleaned_data["user"]
        if self.slot_template.shift_template.slot_templates.filter(
            attendance_template__user=user
        ).exists():
            raise ValidationError(
                _(
                    "This user is already registered to another slot in this ABCD shift."
                ),
                code="invalid",
            )
        return user


class ShiftAttendanceForm(forms.ModelForm):
    user = TapirUserChoiceField()

    class Meta:
        model = ShiftAttendance
        fields = ["user"]


class ShiftUserDataForm(forms.ModelForm):
    class Meta:
        model = ShiftUserData
        fields = ["capabilities", "attendance_mode"]
        widgets = {
            "capabilities": CheckboxSelectMultiple(
                choices=SHIFT_USER_CAPABILITY_CHOICES.items()
            )
        }
