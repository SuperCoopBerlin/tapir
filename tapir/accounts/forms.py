from django import forms
from django.contrib.auth import forms as auth_forms

from tapir.accounts.models import TapirUser
from tapir.utils.forms import DateInput, TapirPhoneNumberField


class TapirUserForm(forms.ModelForm):
    phone_number = TapirPhoneNumberField(required=False)

    class Meta:
        model = TapirUser
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
        ]
        widgets = {
            "birthdate": DateInput(),
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
