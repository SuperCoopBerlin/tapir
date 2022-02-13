from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, CheckboxSelectMultiple, BooleanField
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from tapir.accounts.models import TapirUser
from tapir.shifts.models import (
    Shift,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftUserData,
    SHIFT_USER_CAPABILITY_CHOICES,
    ShiftSlotTemplate,
    ShiftSlot,
    ShiftAccountEntry,
    ShiftExemption,
)
from tapir.utils.forms import DateInput


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


class MissingCapabilitiesWarningMixin(forms.Form):
    confirm_missing_capabilities = BooleanField(
        label=_(
            "I have read the warning about the missing qualification and confirm that the user should get registered to the shift"
        ),
        required=False,
        widget=HiddenInput,
    )

    def validate_unique(self):
        super().validate_unique()
        if "user" in self._errors:
            return

        user: TapirUser = self.cleaned_data["user"]

        if (
            "confirm_missing_capabilities" in self.cleaned_data
            and not self.cleaned_data["confirm_missing_capabilities"]
        ):
            missing_capabilities = [
                _(SHIFT_USER_CAPABILITY_CHOICES[capability])
                for capability in self.get_required_capabilities()
                if capability not in user.shift_user_data.capabilities
            ]
            if len(missing_capabilities) > 0:
                error_msg = _(
                    f"The selected user is missing the required qualification for this shift : {missing_capabilities}"
                )
                self.add_error("user", error_msg)
                self.fields[
                    "confirm_missing_capabilities"
                ].widget = forms.CheckboxInput()
                self.fields["confirm_missing_capabilities"].required = True


class ShiftAttendanceTemplateForm(MissingCapabilitiesWarningMixin, forms.ModelForm):
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
        user: TapirUser = self.cleaned_data["user"]
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

    def get_required_capabilities(self):
        return self.slot_template.required_capabilities


class ShiftAttendanceForm(MissingCapabilitiesWarningMixin, forms.ModelForm):
    user = TapirUserChoiceField()

    class Meta:
        model = ShiftAttendance
        fields = ["user"]

    def __init__(self, *args, **kwargs):
        self.slot = ShiftSlot.objects.get(pk=kwargs.pop("slot_pk", None))
        super().__init__(*args, **kwargs)

    def clean_user(self):
        user = self.cleaned_data["user"]
        if self.slot.shift.slots.filter(attendances__user=user).exists():
            raise ValidationError(
                _("This user is already registered to another slot in this shift."),
                code="invalid",
            )
        return user

    def get_required_capabilities(self):
        return self.slot.required_capabilities


class ShiftUserDataForm(forms.ModelForm):
    capabilities = forms.MultipleChoiceField(
        required=False,
        choices=SHIFT_USER_CAPABILITY_CHOICES.items(),
        widget=CheckboxSelectMultiple,
        label=_("Qualifications"),
    )

    class Meta:
        model = ShiftUserData
        fields = ["attendance_mode", "capabilities"]


class CreateShiftAccountEntryForm(forms.ModelForm):
    class Meta:
        model = ShiftAccountEntry
        fields = ["date", "value", "description"]
        widgets = {
            "date": forms.widgets.DateTimeInput(attrs={"type": "datetime-local"})
        }


class UpdateShiftAttendanceForm(forms.ModelForm):
    class Meta:
        model = ShiftAttendance
        fields = ["state"]

    description = forms.CharField()

    def __init__(self, *args, **kwargs):
        state = kwargs.pop("state")
        super(UpdateShiftAttendanceForm, self).__init__(*args, **kwargs)
        self.initial["state"] = state


class ShiftExemptionForm(forms.ModelForm):
    class Meta:
        model = ShiftExemption
        fields = ["start_date", "end_date", "description"]
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
        }

    confirm_cancelled_attendances = BooleanField(
        label=_(
            "I have read the warning about the cancelled attendances and confirm that the exemption should be created"
        ),
        required=False,
        widget=HiddenInput,
    )
    confirm_cancelled_abcd_attendances = BooleanField(
        label=_(
            "I have read the warning about the cancelled ABCD attendances and confirm that the exemption should be "
            "created "
        ),
        required=False,
        widget=HiddenInput,
    )

    def clean(self):
        super().clean()
        if (
            "confirm_cancelled_attendances" in self._errors
            or "confirm_cancelled_abcd_attendances" in self._errors
        ):
            return

        user = self.instance.shift_user_data.user
        if (
            "confirm_cancelled_attendances" in self.cleaned_data
            and not self.cleaned_data["confirm_cancelled_attendances"]
        ):
            covered_attendances = ShiftExemption.get_attendances_cancelled_by_exemption(
                user=user,
                start_date=self.cleaned_data["start_date"],
                end_date=self.cleaned_data["end_date"],
            )
            if covered_attendances.count() > 0:
                attendances_display = ", ".join(
                    [
                        attendance.slot.get_display_name()
                        for attendance in covered_attendances
                    ]
                )
                error_msg = _(
                    f"The user will be unregistered from the following shifts because they are within the range of "
                    f"the exemption : {attendances_display} "
                )
                self.add_error("confirm_cancelled_attendances", error_msg)
                self.fields[
                    "confirm_cancelled_attendances"
                ].widget = forms.CheckboxInput()
                self.fields["confirm_cancelled_attendances"].required = True

        if (
            "confirm_cancelled_abcd_attendances" in self.cleaned_data
            and not self.cleaned_data["confirm_cancelled_abcd_attendances"]
            and ShiftExemption.must_unregister_from_abcd_shift(
                start_date=self.cleaned_data["start_date"],
                end_date=self.cleaned_data["end_date"],
            )
        ):
            attendance_templates = ShiftAttendanceTemplate.objects.filter(user=user)
            if attendance_templates.count() > 0:
                attendances_display = ", ".join(
                    [
                        attendance.slot_template.get_display_name()
                        for attendance in attendance_templates
                    ]
                )
                error_msg = _(
                    f"The user will be unregistered from the following ABCD shifts because the exemption is longer"
                    f" than {ShiftExemption.THRESHOLD_NB_CYCLES_UNREGISTER_FROM_ABCD_SHIFT} cycles: "
                    f"{attendances_display}"
                )
                self.add_error("confirm_cancelled_abcd_attendances", error_msg)
                self.fields[
                    "confirm_cancelled_abcd_attendances"
                ].widget = forms.CheckboxInput()
                self.fields["confirm_cancelled_abcd_attendances"].required = True
