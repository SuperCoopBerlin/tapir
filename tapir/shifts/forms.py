import datetime

from django import forms
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import (
    ModelChoiceField,
    CheckboxSelectMultiple,
    BooleanField,
)
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.core.models import FeatureFlag
from tapir.settings import PERMISSION_SHIFTS_MANAGE
from tapir.shifts.config import FEATURE_FLAG_SHIFT_PARTNER
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
    ShiftAttendanceMode,
    ShiftWatch,
    StaffingStatusChoices,
    get_staffingstatus_defaults,
    get_staffingstatus_choices,
)
from tapir.utils.forms import DateInputTapir
from tapir.utils.user_utils import UserUtils


class ShiftCreateForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "name",
            "start_time",
            "end_time",
            "num_required_attendances",
            "description",
            "flexible_time",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the max value for num_required_attendances based on available ShiftSlotTemplates
        if self.instance and self.instance.id:
            shift_slot_count = ShiftSlot.objects.filter(shift=self.instance).count()
            self.fields["num_required_attendances"].widget.attrs[
                "max"
            ] = shift_slot_count


class ShiftDeleteForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = []

    confirm_understood = BooleanField(
        label=_("I understand the consequences of deleting a shift"),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.shift = kwargs.pop("shift")
        super().__init__(*args, **kwargs)

    def clean(self):
        attendances_not_cancelled = ShiftAttendance.objects.filter(
            slot__shift=self.shift
        ).exclude(state=ShiftAttendance.State.CANCELLED)
        if attendances_not_cancelled.exists():
            members = [
                UserUtils.build_display_name(
                    attendance.user, UserUtils.DISPLAY_NAME_TYPE_FULL
                )
                for attendance in attendances_not_cancelled
            ]
            raise ValidationError(
                _(
                    f"In order to delete a shift, all member attendances must be set to 'Cancelled'. "
                    f"The following attendances must be updated: {", ".join(members)}"
                )
            )
        return super().clean()


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
        return UserUtils.build_display_name(obj, UserUtils.DISPLAY_NAME_TYPE_FULL)


class ShareOwnerChoiceField(ModelChoiceField):
    widget = Select2Widget()

    def __init__(self, queryset=None, **kwargs):
        if queryset is None:
            queryset = ShareOwner.objects.all()
        queryset = queryset.prefetch_related("user")
        super().__init__(queryset=queryset, **kwargs)

    def label_from_instance(self, obj: ShareOwner):
        return UserUtils.build_display_name(obj, UserUtils.DISPLAY_NAME_TYPE_FULL)


class MissingCapabilitiesWarningMixin(forms.Form):
    confirm_missing_capabilities = BooleanField(
        label=_(
            "I have read the warning about the missing qualification and confirm that the user should get registered to the shift"
        ),
        required=False,
        widget=HiddenInput,
    )

    def get_required_capabilities(self):
        raise NotImplementedError(
            f"Children of {self.__class__} must implement get_required_capabilities()"
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
                    f"The selected user is missing the required qualification for this shift : {missing_capabilities}"
                )
                self.add_error("user", error_msg)
                self.fields["confirm_missing_capabilities"].widget = (
                    forms.CheckboxInput()
                )
                self.fields["confirm_missing_capabilities"].required = True


class CustomTimeCleanMixin(forms.Form):
    custom_time = forms.TimeField(
        required=False, widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.get_shift_object().flexible_time:
            self.fields["custom_time"].required = True
        else:
            self.fields["custom_time"].required = False
            self.fields["custom_time"].widget = HiddenInput()

    def clean_custom_time(self):
        custom_time = self.cleaned_data["custom_time"]
        shift_object = self.get_shift_object()
        if not shift_object.flexible_time:
            return custom_time

        error = self.check_custom_time_is_valid(
            custom_time,
            shift_object.start_time,
            shift_object.end_time,
        )
        if error:
            self.add_error("custom_time", error)

        return custom_time

    @staticmethod
    def check_custom_time_is_valid(chosen_time, start_time, end_time):
        if isinstance(start_time, datetime.datetime):
            start_time = start_time.time()
        if chosen_time < start_time:
            return _("Please set the chosen time after the start of the shift")

        if isinstance(end_time, datetime.datetime):
            end_time = end_time.time()
        if chosen_time > end_time:
            return _("Please set the chosen time before the end of the shift")

        return None

    def get_shift_object(self) -> Shift | ShiftTemplate:
        raise NotImplementedError(
            f"Children of {self.__class__} must implement get_shift_object"
        )


class ShiftAttendanceTemplateForm(
    MissingCapabilitiesWarningMixin, CustomTimeCleanMixin, forms.ModelForm
):
    user = TapirUserChoiceField()
    slot_template: ShiftSlotTemplate

    class Meta:
        model = ShiftAttendanceTemplate
        fields = ["user", "custom_time"]

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

    def get_shift_object(self) -> Shift | ShiftTemplate:
        return self.slot_template.shift_template


class RegisterUserToShiftSlotForm(
    CustomTimeCleanMixin, MissingCapabilitiesWarningMixin, forms.Form
):
    user = TapirUserChoiceField()
    is_solidarity = BooleanField(required=False, label="Mark as a Solidarity Shift")
    field_order = ["user", "is_solidarity", "custom_time"]

    def __init__(self, *args, **kwargs):
        self.slot: ShiftSlot = kwargs.pop("slot")
        self.request_user: TapirUser = kwargs.pop("request_user")
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

    def get_shift_object(self) -> Shift | ShiftTemplate:
        return self.slot.shift

    def clean(self):
        if self.get_shift_object().deleted:
            raise ValidationError(
                _("This shift has been deleted. It is not possible to register to it.")
            )
        return super().clean()


class ShiftUserDataForm(forms.ModelForm):
    class Meta:
        model = ShiftUserData
        fields = ["capabilities"]

    confirm_delete_abcd_attendance = BooleanField(
        label=_(
            "I am aware that the member will be unregistered from their ABCD shift"
        ),
        required=False,
        widget=HiddenInput,
    )
    capabilities = forms.MultipleChoiceField(
        required=False,
        choices=SHIFT_USER_CAPABILITY_CHOICES.items(),
        widget=CheckboxSelectMultiple,
        label=_("Qualifications"),
    )
    shift_partner = TapirUserChoiceField(required=False)

    def __init__(self, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(**kwargs)
        if not FeatureFlag.get_flag_value(FEATURE_FLAG_SHIFT_PARTNER):
            self.fields["shift_partner"].disabled = True
            self.fields["shift_partner"].widget = HiddenInput()
            return

        if self.instance.user.share_owner.is_investing:
            self.fields["shift_partner"].disabled = True

        shift_partner_of: ShiftUserData | None = getattr(
            self.instance, "shift_partner_of", None
        )
        if not shift_partner_of:
            return

        self.fields["shift_partner"].disabled = True
        own_name = UserUtils.build_display_name_for_viewer(
            self.instance.user,
            self.request_user,
        )
        partner_of_name = UserUtils.build_display_name_for_viewer(
            shift_partner_of.user,
            self.request_user,
        )
        self.fields["shift_partner"].help_text = _(
            f"{own_name} is already partner of {partner_of_name}, they can't have a partner of their own"
        )

    def clean_shift_partner(self):
        shift_partner: TapirUser | None = self.cleaned_data.get("shift_partner", None)
        if not shift_partner:
            return shift_partner

        if not shift_partner.share_owner.is_investing:
            self.add_error(
                "shift_partner",
                _("The selected member must be an investing member."),
            )
            return shift_partner

        partner_of_partner = getattr(
            shift_partner.shift_user_data, "shift_partner", None
        )
        if partner_of_partner:
            target_partner_name = UserUtils.build_display_name_for_viewer(
                shift_partner, self.request_user
            )
            partner_of_partner_name = UserUtils.build_display_name_for_viewer(
                partner_of_partner.user,
                self.request_user,
            )
            self.add_error(
                "shift_partner",
                f"{target_partner_name} is already the partner of {partner_of_partner_name}",
            )
            return shift_partner

        partner_is_partner_of: ShiftUserData | None = getattr(
            shift_partner.shift_user_data, "shift_partner_of", None
        )
        if not partner_is_partner_of or partner_is_partner_of == self.instance:
            return shift_partner

        partner_name = UserUtils.build_display_name_for_viewer(
            shift_partner, self.request_user
        )
        partner_of_name = UserUtils.build_display_name_for_viewer(
            partner_is_partner_of.user,
            self.request_user,
        )
        self.add_error(
            "shift_partner",
            f"{partner_name} is already the partner of {partner_of_name}",
        )
        return shift_partner

    def clean(self):
        result = super().clean()

        attendance_mode = self.cleaned_data.get("attendance_mode", None)
        if attendance_mode is None or attendance_mode == ShiftAttendanceMode.REGULAR:
            return result

        confirmation_checkbox_not_ticked = (
            "confirm_delete_abcd_attendance" in self.cleaned_data
            and not self.cleaned_data["confirm_delete_abcd_attendance"]
        )
        user_is_registered_to_an_abcd_shift = ShiftAttendanceTemplate.objects.filter(
            user=self.instance.user
        ).exists()
        if user_is_registered_to_an_abcd_shift and confirmation_checkbox_not_ticked:
            error_msg = _(
                "This member is registered to at least one ABCD shift. "
                "Please confirm the change of attendance mode with the checkbox below."
            )
            self.add_error("attendance_mode", error_msg)
            self.fields["confirm_delete_abcd_attendance"].widget = forms.CheckboxInput()
            self.fields["confirm_delete_abcd_attendance"].required = True

        return result


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
                self.fields["confirm_cancelled_attendances"].widget = (
                    forms.CheckboxInput()
                )
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
                self.fields["confirm_cancelled_abcd_attendances"].widget = (
                    forms.CheckboxInput()
                )
                self.fields["confirm_cancelled_abcd_attendances"].required = True


class ShiftCancelForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["cancelled_reason"]

    def clean(self):
        if self.instance.deleted:
            raise ValidationError(
                _("This shift has been deleted. It is not possible to cancel it.")
            )
        return super().clean()


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
            "start_date",
            "flexible_time",
        ]
        widgets = {
            "start_time": forms.widgets.TimeInput(
                attrs={"type": "time"}, format="%H:%M"
            ),
            "end_time": forms.widgets.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "start_date": DateInputTapir(),
        }

    check_update_future_shifts = BooleanField(
        label=_(
            "I understand that updating this ABCD shift will update all the corresponding future shifts"
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the max value for num_required_attendances based on available ShiftSlotTemplates
        if self.instance and self.instance.id:
            shift_slot_count = ShiftSlotTemplate.objects.filter(
                shift_template=self.instance
            ).count()
            self.fields["num_required_attendances"].widget.attrs[
                "max"
            ] = shift_slot_count


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


class ConvertShiftExemptionToMembershipPauseForm(forms.Form):
    confirm = BooleanField(
        label=_(
            "I understand that this will delete the shift exemption and create a membership pause"
        ),
        required=True,
    )


class ShiftAttendanceCustomTimeForm(CustomTimeCleanMixin, forms.ModelForm):
    class Meta:
        model = ShiftAttendance
        fields = ["custom_time"]

    def get_shift_object(self) -> Shift | ShiftTemplate:
        return self.instance.slot.shift


class ShiftAttendanceTemplateCustomTimeForm(CustomTimeCleanMixin, forms.ModelForm):
    class Meta:
        model = ShiftAttendanceTemplate
        fields = ["custom_time"]

    def get_shift_object(self) -> Shift | ShiftTemplate:
        return self.instance.slot_template.shift_template


class ShiftWatchForm(forms.ModelForm):
    class Meta:
        model = ShiftWatch
        fields = ["staffing_status"]

    staffing_status = forms.MultipleChoiceField(
        required=False,
        choices=get_staffingstatus_choices,
        label=_("Which shift-events do you want to subscribe to?"),
        widget=CheckboxSelectMultiple(),
        disabled=False,
        initial=get_staffingstatus_defaults,
    )
