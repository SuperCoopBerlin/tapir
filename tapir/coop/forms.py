from dateutil.relativedelta import relativedelta
from django import forms
from django.core.exceptions import ValidationError
from django.forms import DateField, IntegerField
from django.utils.translation import gettext_lazy as _

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
    IncomingPayment,
    MembershipPause,
    MembershipResignation,
)
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
            "usage_name",
            "pronouns",
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

    class Meta:
        model = DraftUser
        fields = [
            "first_name",
            "last_name",
            "usage_name",
            "pronouns",
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
            "usage_name",
            "pronouns",
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
                "first_name",
                "last_name",
                "usage_name",
                "pronouns",
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


class MembershipPauseForm(forms.ModelForm):
    class Meta:
        model = MembershipPause
        fields = ["share_owner", "description", "start_date", "end_date"]
        widgets = {
            "start_date": DateInputTapir(),
            "end_date": DateInputTapir(),
        }

    share_owner = ShareOwnerChoiceField()


class MembershipResignationForm(forms.ModelForm):
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 2, "placeholder": _("Please not more than 1000 characters.")}
        ),
    )
    share_owner = ShareOwnerChoiceField()
    transferring_shares_to = ShareOwnerChoiceField(
        required=False,
        label=_("Transferring share(s) to"),
        help_text=MembershipResignation._meta.get_field(
            "transferring_shares_to"
        ).help_text,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields["share_owner"].disabled = True
            self.fields["transferring_shares_to"].disabled = True
            self.fields["resignation_type"].disabled = True

    class Meta:
        model = MembershipResignation
        fields = [
            "share_owner",
            "cancellation_reason",
            "cancellation_date",
            "resignation_type",
            "transferring_shares_to",
            "paid_out",
        ]
        widgets = {"cancellation_date": DateInputTapir()}

    def clean(self):
        cleaned_data = super().clean()
        share_owner: ShareOwner = cleaned_data.get("share_owner")
        resignation_type = cleaned_data.get("resignation_type")
        cancellation_date = cleaned_data.get("cancellation_date")
        transferring_shares_to = cleaned_data.get("transferring_shares_to")
        paid_out = cleaned_data.get("paid_out")

        self.validate_share_owner(share_owner)
        self.validate_transfer_choice(resignation_type, transferring_shares_to)
        self.validate_duplicates(share_owner, transferring_shares_to)
        self.validate_if_gifted(resignation_type, paid_out)

        if resignation_type == MembershipResignation.ResignationType.BUY_BACK:
            self.cleaned_data["pay_out_day"] = cancellation_date + relativedelta(
                day=31, month=12, years=3
            )
        else:
            self.cleaned_data["pay_out_day"] = cancellation_date
            self.cleaned_data["paid_out"] = True

        return cleaned_data

    def validate_share_owner(self, share_owner):
        if MembershipResignation.objects.filter(
            share_owner__id=share_owner.id
        ).exists():
            self.add_error(
                "share_owner",
                ValidationError(_("This member is already resigned.")),
            )

    def validate_transfer_choice(self, resignation_type, transferring_shares_to):
        if (
            resignation_type == MembershipResignation.ResignationType.TRANSFER
            and transferring_shares_to is None
        ):
            self.add_error(
                "transferring_shares_to",
                ValidationError(
                    _(
                        "Please select the member that the shares should be transferred to."
                    )
                ),
            )

        if (
            resignation_type != MembershipResignation.ResignationType.TRANSFER
            and transferring_shares_to is not None
        ):
            self.add_error(
                "transferring_shares_to",
                ValidationError(
                    _(
                        "If the shares don't get transferred to another member, this field should be empty."
                    )
                ),
            )

    def validate_duplicates(self, share_owner, transferring_shares_to):
        if transferring_shares_to == share_owner:
            self.add_error(
                "transferring_shares_to",
                ValidationError(
                    _(
                        "Sender and receiver of transferring the share(s) cannot be the same."
                    )
                ),
            )

    def validate_if_gifted(self, resignation_type, paid_out):
        if paid_out and (
            resignation_type
            in [
                MembershipResignation.ResignationType.TRANSFER,
                MembershipResignation.ResignationType.GIFT_TO_COOP,
            ]
        ):
            self.add_error(
                "paid_out",
                ValidationError(_("Cannot pay out, because shares have been gifted.")),
            )
