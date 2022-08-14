from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.forms import DateField, IntegerField, BooleanField
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.config import (
    COOP_SHARE_PRICE,
    COOP_MIN_SHARES,
    COOP_MAX_SHARES,
    COOP_DEFAULT_SHARES,
)
from tapir.coop.models import (
    ShareOwnership,
    DraftUser,
    ShareOwner,
    FinancingCampaign,
    IncomingPayment,
)
from tapir.coop.pdfs import get_membership_agreement_pdf
from tapir.settings import FROM_EMAIL_MEMBER_OFFICE
from tapir.shifts.forms import ShareOwnerChoiceField
from tapir.utils.forms import DateInputTapir, TapirPhoneNumberField


class ShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = [
            "start_date",
            "end_date",
            "amount_paid",
        ]
        widgets = {
            "start_date": DateInputTapir(),
            "end_date": DateInputTapir(),
        }


class ShareOwnershipCreateMultipleForm(forms.Form):
    start_date = DateField(
        label=_("Start date"),
        required=True,
        widget=DateInputTapir,
        help_text=_(
            "Usually, the date on the membership agreement, or today. "
            "In the case of sold or gifted shares, can be set in the future."
        ),
    )
    end_date = DateField(
        label=_("End date"),
        required=False,
        widget=DateInputTapir,
        help_text=_(
            "Usually left empty. "
            "Can be set to a point in the future "
            "if it is already known that the shares will be transferred to another member in the future."
        ),
    )
    num_shares = IntegerField(
        label=_("Number of shares to create"), required=True, min_value=1
    )
    send_confirmation_email = BooleanField(
        label=_("Send confirmation email"), initial=True
    )

    def clean_end_date(self):
        if (
            self.cleaned_data["end_date"]
            and self.cleaned_data["end_date"] < self.cleaned_data["start_date"]
        ):
            raise ValidationError(_("The end date must be later than the start date."))
        return self.cleaned_data["end_date"]


class DraftUserForm(forms.ModelForm):
    phone_number = TapirPhoneNumberField(required=False)

    class Meta:
        model = DraftUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "country",
            "preferred_language",
            "is_investing",
            "attended_welcome_session",
            "ratenzahlung",
            "paid_membership_fee",
            "paid_shares",
            "signed_membership_agreement",
            "num_shares",
        ]
        widgets = {
            "birthdate": DateInputTapir(),
        }


class DraftUserRegisterForm(forms.ModelForm):
    phone_number = TapirPhoneNumberField()
    num_shares = forms.IntegerField(
        label=_("Number of Shares"),
        initial=COOP_DEFAULT_SHARES,
        min_value=COOP_MIN_SHARES,
        max_value=COOP_MAX_SHARES,
        help_text=_(
            "Number of shares you would like to purchase. The price of one share is EUR %(share_price)s. "
            "You need to purchase at least one share to become member of the cooperative. "
            "To support our cooperative even more, you may voluntarily purchase more shares."
        )
        % {"share_price": COOP_SHARE_PRICE},
    )
    is_investing = forms.BooleanField(
        initial=False,
        required=False,
        label=_(
            "I would like to join the membership list as an investing member (= sponsoring member)"
        ),
        help_text=_(
            "<b>Note</b>: Investing members are sponsoring members. They have no voting rights in the General "
            "Assembly and cannot use the services of the cooperative that are exclusive to ordinary members. "
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True

    def save(self, commit=True):
        draft_user: DraftUser = super().save(commit)
        with translation.override(draft_user.preferred_language):
            mail = EmailMessage(
                subject=_("Welcome at %(organisation_name)s!")
                % {"organisation_name": settings.COOP_NAME},
                body=render_to_string(
                    [
                        "coop/email/membership_confirmation_welcome.html",
                        "coop/email/membership_confirmation_welcome.default.html",
                    ],
                    {
                        "owner": draft_user,
                        "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
                    },
                ),
                from_email=FROM_EMAIL_MEMBER_OFFICE,
                to=[draft_user.email],
                attachments=[
                    (
                        "Beteiligungserklärung %s.pdf" % draft_user.get_display_name(),
                        get_membership_agreement_pdf(draft_user).write_pdf(),
                        "application/pdf",
                    )
                ],
            )
            mail.content_subtype = "html"
            mail.send()
        return draft_user

    class Meta:
        model = DraftUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "country",
            "preferred_language",
        ]
        required = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birthdate",
            "street",
            "postcode",
            "city",
            "country",
            "preferred_language",
        ]
        widgets = {"birthdate": DateInputTapir()}


class ShareOwnerForm(forms.ModelForm):
    class Meta:
        model = ShareOwner
        fields = [
            "is_company",
            "company_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "preferred_language",
            "is_investing",
            "ratenzahlung",
            "attended_welcome_session",
            "paid_membership_fee",
            "willing_to_gift_a_share",
        ]
        widgets = {
            "birthdate": DateInputTapir(),
            "willing_to_gift_a_share": DateInputTapir(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.user:
            for f in [
                "is_company",
                "company_name",
                "first_name",
                "last_name",
                "email",
                "birthdate",
                "street",
                "street_2",
                "postcode",
                "city",
                "preferred_language",
                "phone_number",
            ]:
                del self.fields[f]


class FinancingCampaignForm(forms.ModelForm):
    class Meta:
        model = FinancingCampaign
        fields = [
            "name",
            "is_active",
            "goal",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for source in self.instance.sources.all():
            self.fields[f"financing_source_{source.id}"] = forms.IntegerField(
                required=True, label=_(source.name), initial=source.raised_amount
            )

    def save(self, commit=True):
        for source in self.instance.sources.all():
            source.raised_amount = self.cleaned_data[f"financing_source_{source.id}"]
            source.save()
        return super().save(commit=commit)


class IncomingPaymentForm(forms.ModelForm):
    class Meta:
        model = IncomingPayment
        fields = [
            "paying_member",
            "credited_member",
            "amount",
            "payment_date",
            "comment",
        ]
        widgets = {
            "payment_date": DateInputTapir(),
            "creation_date": DateInputTapir(),
        }

    paying_member = ShareOwnerChoiceField()
    credited_member = ShareOwnerChoiceField(
        help_text=_(
            "Usually, the credited member is the same as the paying member. "
            "Only if a person if gifting another person a share through the matching program, "
            "then the fields can be different."
        )
    )
