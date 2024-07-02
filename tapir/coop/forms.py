from django.utils import timezone
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
    TapirUser,
)
from tapir.shifts.forms import ShareOwnerChoiceField, TapirUserChoiceField
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
    coop_buys_shares_back = forms.BooleanField(
        label=_("Coop buys back share(s)"), required=False
    )
    willing_to_gift_shares_to_coop = forms.BooleanField(required=False)
    share_owner = ShareOwnerChoiceField()
    transfering_shares_to = ShareOwnerChoiceField(
        required=False, label=_("Transfering share(s) to")
    )

    class Meta:
        model = MembershipResignation
        fields = [
            "share_owner",
            "cancellation_reason",
            "cancellation_date",
            "coop_buys_shares_back",
            "willing_to_gift_shares_to_coop",
            "transfering_shares_to",
            "paid_out",
        ]
        widgets = {"cancellation_date": DateInputTapir()}

    def clean(self):
        cleaned_data = super().clean()
        coop_buys_shares_back = cleaned_data.get("coop_buys_shares_back")
        willing_to_gift_shares_to_coop = cleaned_data.get(
            "willing_to_gift_shares_to_coop"
        )
        transfering_shares_to = cleaned_data.get("transfering_shares_to")
        cancellation_date = cleaned_data.get("cancellation_date")

        self.validate_share_owner()
        self.validate_choices()
        self.validate_duplicates()
        self.validate_if_gifted()

        if coop_buys_shares_back:
            self.instance.pay_out_day = cancellation_date + relativedelta(
                day=31, month=12, years=3
            )
        if willing_to_gift_shares_to_coop or transfering_shares_to != None:
            self.cleaned_data["pay_out_day"] = cancellation_date
            self.cleaned_data["paid_out"] = True

    def validate_share_owner(self):
        share_owner = self.cleaned_data.get("share_owner")
        if self.instance.pk is not None:
            return share_owner

        if MembershipResignation.objects.filter(
            share_owner__id=share_owner.id
        ).exists():
            self.add_error(
                "share_owner",
                ValidationError(_("This member is already resigned.")),
            )
        return share_owner

    def validate_choices(self):
        coop_buys_shares_back = self.cleaned_data.get("coop_buys_shares_back")
        willing_to_gift_shares_to_coop = self.cleaned_data.get(
            "willing_to_gift_shares_to_coop"
        )
        transfering_shares_to = self.cleaned_data.get("transfering_shares_to")
        only_one_choice_allowed_error_message = _("Please take only one choice.")

        if coop_buys_shares_back and willing_to_gift_shares_to_coop:
            self.add_error(
                "coop_buys_shares_back", only_one_choice_allowed_error_message
            )
            self.add_error(
                "willing_to_gift_shares_to_coop", only_one_choice_allowed_error_message
            )
        elif transfering_shares_to != None and (
            coop_buys_shares_back or willing_to_gift_shares_to_coop
        ):
            self.add_error(
                "transfering_shares_to", only_one_choice_allowed_error_message
            )
            if coop_buys_shares_back:
                self.add_error(
                    "coop_buys_shares_back", only_one_choice_allowed_error_message
                )
            elif willing_to_gift_shares_to_coop:
                self.add_error(
                    "willing_to_gift_shares_to_coop",
                    only_one_choice_allowed_error_message,
                )

        if (
            transfering_shares_to == None
            and not willing_to_gift_shares_to_coop
            and not coop_buys_shares_back
        ):
            make_at_least_one_choice_error_message = "Please make a least one choice."
            self.add_error(
                "transfering_shares_to",
                ValidationError(_(make_at_least_one_choice_error_message)),
            )
            self.add_error(
                "willing_to_gift_shares_to_coop",
                ValidationError(_(make_at_least_one_choice_error_message)),
            )
            self.add_error(
                "coop_buys_shares_back",
                ValidationError(_(make_at_least_one_choice_error_message)),
            )
        return (
            coop_buys_shares_back,
            willing_to_gift_shares_to_coop,
            transfering_shares_to,
        )

    def validate_duplicates(self):
        transfering_shares_to = self.cleaned_data.get("transfering_shares_to")
        share_owner = self.cleaned_data.get("share_owner")
        if transfering_shares_to == share_owner:
            self.add_error(
                "transfering_shares_to",
                ValidationError(
                    _(
                        "Sender and receiver of tranfering the share(s) cannot be the same."
                    )
                ),
            )
        return transfering_shares_to, share_owner

    def validate_if_gifted(self):
        transfering_shares_to = self.cleaned_data.get("transfering_shares_to")
        willing_to_gift_shares_to_coop = self.cleaned_data.get(
            "willing_to_gift_shares_to_coop"
        )
        paid_out = self.cleaned_data.get("paid_out")

        if paid_out and (
            transfering_shares_to != None or willing_to_gift_shares_to_coop
        ):
            self.add_error(
                "paid_out",
                ValidationError(_("Cannot pay out, because shares have been gifted.")),
            )
        return transfering_shares_to, willing_to_gift_shares_to_coop, paid_out
