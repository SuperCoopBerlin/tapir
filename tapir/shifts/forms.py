from django import forms
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import ModelChoiceField, CheckboxSelectMultiple, BooleanField
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.settings import PERMISSION_SHIFTS_MANAGE
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
    SHIFT_SLOT_WARNING_CHOICES,
    ShiftTemplate,
)
from tapir.utils.forms import DateInputTapir


class ShiftCreateForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "name",
            "start_time",
            "end_time",
            "num_required_attendances",
            "description",
        ]
        widgets = {
            "start_time": forms.widgets.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "end_time": forms.widgets.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def clean_end_time(self):
        if self.cleaned_data["end_time"] <= self.cleaned_data["start_time"]:
            raise ValidationError(
                _("The shift must end after it starts."),
                code="invalid",
            )

        return self.cleaned_data["end_time"]


class ShiftSlotForm(forms.ModelForm):
    class Meta:
        model = ShiftSlot
        fields = ["name", "required_capabilities", "warnings"]
        widgets = {
            "required_capabilities": forms.widgets.CheckboxSelectMultiple(
                choices=SHIFT_USER_CAPABILITY_CHOICES.items()
            ),
            "warnings": forms.widgets.CheckboxSelectMultiple(
                choices=SHIFT_SLOT_WARNING_CHOICES.items()
            ),
        }


class TapirUserChoiceField(ModelChoiceField):
    widget = Select2Widget()

    def __init__(
        self, queryset=TapirUser.objects.filter(share_owner__isnull=False), **kwargs
    ):
        queryset = queryset.prefetch_related("share_owner")
        super().__init__(queryset=queryset, **kwargs)

    def label_from_instance(self, obj: TapirUser):
        share_owner_id = obj.share_owner.id if hasattr(obj, "share_owner") else ""
        return f"{obj.first_name} {obj.last_name} ({share_owner_id})"


class ShareOwnerChoiceField(ModelChoiceField):
    widget = Select2Widget()

    def __init__(self, queryset=ShareOwner.objects.all(), **kwargs):
        queryset = queryset.prefetch_related("user")
        super().__init__(queryset=queryset, **kwargs)

    def label_from_instance(self, obj: ShareOwner):
        return f"{obj.get_info().first_name} {obj.get_info().last_name} ({obj.id})"


class MissingCapabilitiesWarningMixin(forms.Form):
    confirm_missing_capabilities = BooleanField(
        label=_(
            "I have read the warning about the missing qualification and confirm that the user should get registered to the shift"
        ),
        required=False,
        widget=HiddenInput,
    )

    def clean(self):
        super().clean()
        if "user" in self._errors:
            return

        user_to_register: TapirUser = self.cleaned_data["user"]
        if (
            "confirm_missing_capabilities" in self.cleaned_data
            and not self.cleaned_data["confirm_missing_capabilities"]
        ):
            missing_capabilities = [
                _(SHIFT_USER_CAPABILITY_CHOICES[capability])
                for capability in self.get_required_capabilities()
                if capability not in user_to_register.shift_user_data.capabilities
            ]
            if len(missing_capabilities) > 0:
                error_msg = _(
                    f"The selected user is missing the required qualification for this shift: {missing_capabilities}"
                )
                self.add_error("user", error_msg)
                self.fields[
                    "confirm_missing_capabilities"
                ].widget = forms.CheckboxInput()
                self.fields["confirm_missing_capabilities"].required = True


class ShiftAttendanceTemplateForm(MissingCapabilitiesWarningMixin, forms.ModelForm):
    user = TapirUserChoiceField()
    slot_template: ShiftSlotTemplate

    class Meta:
        model = ShiftAttendanceTemplate
        fields = ["user"]

    def __init__(self, *args, **kwargs):
        self.slot_template = ShiftSlotTemplate.objects.get(
            pk=kwargs.pop("slot_template_pk", None)
        )
        super().__init__(*args, **kwargs)
        for warning in self.slot_template.warnings:
            self.fields[f"warning_{warning}"] = forms.BooleanField(
                label=SHIFT_SLOT_WARNING_CHOICES[warning]
            )

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


class RegisterUserToShiftSlotForm(MissingCapabilitiesWarningMixin):
    user = TapirUserChoiceField()
    request_user: TapirUser
    slot: ShiftSlot

    def __init__(self, *args, **kwargs):
        self.slot = kwargs.pop("slot", None)
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)
        self.fields["user"].disabled = not self.request_user.has_perm(
            PERMISSION_SHIFTS_MANAGE
        )
        for warning in self.slot.warnings:
            self.fields[f"warning_{warning}"] = forms.BooleanField(
                label=SHIFT_SLOT_WARNING_CHOICES[warning]
            )

    def get_required_capabilities(self):
        return self.slot.required_capabilities

    def clean_user_to_register(self):
        user_to_register = self.cleaned_data["user"]
        if (
            not self.request_user.has_perm(PERMISSION_SHIFTS_MANAGE)
            and user_to_register.pk != self.request_user.pk
        ):
            raise PermissionDenied(
                _("You need the shifts.manage permission to do this.")
            )
        if self.slot.shift.slots.filter(attendances__user=user_to_register).exists():
            raise ValidationError(
                _("This user is already registered to another slot in this shift."),
                code="invalid",
            )
        return user_to_register


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
            "date": forms.widgets.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }


class UpdateShiftAttendanceForm(forms.ModelForm):
    class Meta:
        model = ShiftAttendance
        fields = ["state"]

    description = forms.CharField()

    def __init__(self, *args, **kwargs):
        state = kwargs.pop("state")
        super().__init__(*args, **kwargs)
        self.initial["state"] = state


class ShiftExemptionForm(forms.ModelForm):
    class Meta:
        model = ShiftExemption
        fields = ["start_date", "end_date", "description"]
        widgets = {
            "start_date": DateInputTapir(),
            "end_date": DateInputTapir(),
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
            "created"
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
                    f"The member will be unregistered from the following shifts because they are within the range of the exemption : {attendances_display}"
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
            if attendance_templates.exists():
                attendances_display = ", ".join(
                    [
                        attendance.slot_template.get_display_name()
                        for attendance in attendance_templates
                    ]
                )
                error_msg = _(
                    "The user will be unregistered from the following ABCD shifts because the exemption is longer "
                    "than %(number_of_cycles)s cycles: %(attendances_display)s "
                ) % {
                    "number_of_cycles": ShiftExemption.THRESHOLD_NB_CYCLES_UNREGISTER_FROM_ABCD_SHIFT,
                    "attendances_display": attendances_display,
                }
                self.add_error("confirm_cancelled_abcd_attendances", error_msg)
                self.fields[
                    "confirm_cancelled_abcd_attendances"
                ].widget = forms.CheckboxInput()
                self.fields["confirm_cancelled_abcd_attendances"].required = True


class ShiftCancelForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["cancelled_reason"]


class ShiftTemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplate
        fields = [
            "name",
            "description",
            "group",
            "num_required_attendances",
            "weekday",
            "start_time",
            "end_time",
        ]
        widgets = {
            "start_time": forms.widgets.TimeInput(
                attrs={"type": "time"}, format="%H:%M"
            ),
            "end_time": forms.widgets.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    check_update_future_shifts = BooleanField(
        label=_(
            "I understand that updating this ABCD shift will update all the corresponding future shifts"
        ),
        required=True,
    )


class ShiftSlotTemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftSlotTemplate
        fields = ["name", "required_capabilities", "warnings"]
        widgets = {
            "required_capabilities": forms.widgets.CheckboxSelectMultiple(
                choices=SHIFT_USER_CAPABILITY_CHOICES.items()
            ),
            "warnings": forms.widgets.CheckboxSelectMultiple(
                choices=SHIFT_SLOT_WARNING_CHOICES.items()
            ),
        }

    check_update_future_shifts = BooleanField(
        label=_(
            "I understand that adding or editing a slot to this ABCD shift will affect all the corresponding future shifts"
        ),
        required=True,
    )
