from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.forms import TextInput, CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.accounts.models import TapirUser, LdapGroup
from tapir.core.tapir_email_base import mails_not_mandatory, mails_mandatory
from tapir.utils.forms import DateInputTapir, TapirPhoneNumberField


class TapirUserSelfUpdateForm(forms.ModelForm):
    additional_mails = forms.MultipleChoiceField(
        required=False,
        choices=mails_not_mandatory(default=None),
        widget=CheckboxSelectMultiple(),
        label=_("Additional Emails"),
    )

    mandatory_mails = forms.MultipleChoiceField(
        required=False,
        choices=mails_mandatory(default=None),
        label=_("Mandatory Emails"),
        widget=CheckboxSelectMultiple(),
        initial=[m[0] for m in mails_mandatory(default=None)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mandatory_mails"].disabled = True

    class Meta:
        model = TapirUser
        fields = ["usage_name", "pronouns", "additional_mails"]
        widgets = {}


class TapirUserForm(TapirUserSelfUpdateForm):
    phone_number = TapirPhoneNumberField(required=False)

    class Meta(TapirUserSelfUpdateForm.Meta):
        # model = TapirUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "email",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "preferred_language",
            "co_purchaser",
        ] + TapirUserSelfUpdateForm.Meta.fields

        widgets = TapirUserSelfUpdateForm.Meta.widgets | {
            "birthdate": DateInputTapir(),
            "username": TextInput(attrs={"readonly": True}),
        }


class PasswordResetForm(auth_forms.PasswordResetForm):
    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        email_field_name = auth_forms.UserModel.get_email_field_name()
        active_users = auth_forms.UserModel._default_manager.filter(
            **{
                "%s__iexact" % email_field_name: email,
                "is_active": True,
            }
        )
        return (
            u
            for u in active_users
            # Users with unusable passwords in the DB should be able to reset their passwords, the new password will be
            # set in the LDAP instead. See models.LdapUser
            # if u.has_usable_password() and
            if auth_forms._unicode_ci_compare(email, getattr(u, email_field_name))
        )


class EditUserLdapGroupsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tapir_user: TapirUser = kwargs.pop("tapir_user", None)
        super().__init__(*args, **kwargs)
        user_dn = tapir_user.get_ldap().build_dn()
        for group_cn in settings.LDAP_GROUPS:
            self.fields[group_cn] = forms.BooleanField(
                required=False,
                label=group_cn,
                initial=user_dn in LdapGroup.get_group_members_dns(cn=group_cn),
            )


class EditUsernameForm(forms.ModelForm):
    class Meta:
        model = TapirUser
        fields = ["username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.Meta.fields:
            self.fields[field_name].required = True

    def clean_username(self):
        if TapirUser.objects.filter(username=self.cleaned_data["username"]).exists():
            raise ValidationError(_("This username is not available."))

        return self.cleaned_data["username"]
