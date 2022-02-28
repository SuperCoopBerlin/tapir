from django import forms
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop.models import ShareOwnership, DraftUser, ShareOwner, FinancingCampaign
from tapir.coop.pdfs import get_membership_agreement_pdf
from tapir.settings import FROM_EMAIL_MEMBER_OFFICE
from tapir.utils.forms import DateInput, TapirPhoneNumberField


class ShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = [
            "start_date",
            "end_date",
            "amount_paid",
        ]
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
        }


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
            "is_investing",
            "attended_welcome_session",
            "ratenzahlung",
            "paid_membership_fee",
            "paid_shares",
            "signed_membership_agreement",
            "num_shares",
        ]
        widgets = {
            "birthdate": DateInput(),
        }


class DraftUserRegisterForm(forms.ModelForm):
    phone_number = TapirPhoneNumberField()

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
            "preferred_language",
        ]
        widgets = {"birthdate": DateInput()}


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
            "birthdate": DateInput(),
            "willing_to_gift_a_share": DateInput(),
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
