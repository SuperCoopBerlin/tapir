from typing import List

from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.forms import TextInput, CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.accounts.models import TapirUser, OptionalMails
from tapir.core.tapir_email_base import (
    get_mail_types,
)
from tapir.settings import PERMISSION_COOP_ADMIN, GROUP_VORSTAND
from tapir.utils.forms import DateInputTapir, TapirPhoneNumberField


class TapirUserSelfUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = TapirUser
        fields = ["usage_name", "pronouns"]
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
        tapir_user: TapirUser = kwargs.pop("tapir_user")
        request_user: TapirUser = kwargs.pop("request_user")
        super().__init__(*args, **kwargs)
        for group_cn in settings.LDAP_GROUPS:
            self.fields[group_cn] = forms.BooleanField(
                required=False,
                label=group_cn,
                initial=group_cn in tapir_user.get_ldap_user().group_names,
            )

        if not request_user.has_perm(PERMISSION_COOP_ADMIN):
            self.fields[GROUP_VORSTAND].disabled = True


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


def get_optional_mail_choices():
    # this has to be a function so that choices has a callable and is refreshed whenever the form is called
    return [
        (mail.get_unique_id(), mail.get_name())
        for mail in get_mail_types(optional=True, enabled_by_default="both")
    ]


def get_mandatory_mail_choices():
    # this has to be a function so that choices has a callable and is refreshed whenever the form is called
    return [
        (mail.get_unique_id(), mail.get_name())
        for mail in get_mail_types(enabled_by_default="both", optional=False)
    ]


class OptionalMailsForm(forms.Form):

    optional_mails = forms.MultipleChoiceField(
        choices=get_optional_mail_choices,
        widget=forms.CheckboxSelectMultiple(),
        label=_("Optional Mails"),
        required=False,
    )

    mandatory_mails = forms.MultipleChoiceField(
        required=False,
        choices=get_mandatory_mail_choices,
        label=_("Important Mails"),
        widget=CheckboxSelectMultiple(),
        disabled=True,
        initial=[
            m.get_unique_id()
            for m in get_mail_types(enabled_by_default="both", optional=False)
        ],
    )

    def __init__(self, *args, **kwargs):
        tapir_user: TapirUser = kwargs.pop("tapir_user")
        super().__init__(*args, **kwargs)
        self.fields["optional_mails"].initial = (
            tapir_user.get_optional_mail_ids_user_will_receive()
        )
