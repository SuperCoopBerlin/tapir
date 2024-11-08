import datetime
from typing import Self

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum, Count, F, PositiveIntegerField, Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils
from tapir.accounts.models import TapirUser
from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.coop.services.InvestingStatusService import InvestingStatusService
from tapir.coop.services.MembershipPauseService import MembershipPauseService
from tapir.coop.services.NumberOfSharesService import NumberOfSharesService
from tapir.core.config import help_text_displayed_name
from tapir.log.models import UpdateModelLogEntry, ModelLogEntry, LogEntry
from tapir.shifts.services.shift_can_shop_service import ShiftCanShopService
from tapir.utils.expection_utils import TapirException
from tapir.utils.models import (
    DurationModelMixin,
    CountryField,
    positive_number_validator,
)
from tapir.utils.shortcuts import (
    get_html_link,
    ensure_datetime,
)
from tapir.utils.user_utils import UserUtils


class ShareOwner(models.Model):
    """ShareOwner represents a share_owner of a ShareOwnership.

    Usually, this is just a proxy for the associated user. However, it may also be used to
    represent a person or company that does not have their own account.
    """

    class Meta:
        indexes = [models.Index(fields=["is_investing"])]

    # Only for owners that have a user account
    user = models.OneToOneField(
        TapirUser,
        related_name="share_owner",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    is_company = models.BooleanField(
        verbose_name=_("Is company"), default=False, blank=False
    )
    company_name = models.CharField(max_length=150, blank=True)

    # In the case that this is a company, this is the contact data for the company representative
    # There can also be investing members that do not have a user account
    first_name = models.CharField(
        _("Administrative first name"), max_length=150, blank=True
    )
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    usage_name = models.CharField(
        _("Usage name"),
        max_length=150,
        blank=True,
        help_text=_(help_text_displayed_name),
    )
    pronouns = models.CharField(_("Pronouns"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone_number = PhoneNumberField(_("Phone number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
        blank=True,
    )
    is_investing = models.BooleanField(
        verbose_name=_("Is investing member"), default=False
    )
    ratenzahlung = models.BooleanField(verbose_name=_("Ratenzahlung"), default=False)
    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Entrance Fee"), default=True)
    willing_to_gift_a_share = models.DateField(
        _("Is willing to gift a share"), null=True, blank=True
    )
    create_account_reminder_email_sent = models.BooleanField(default=False)

    class ShareOwnerQuerySet(models.QuerySet):
        def with_name(self, search_string: str):
            searches = [s for s in search_string.split(" ") if s != ""]

            combined_filters = Q(last_name__icontains="")
            for search in searches:
                word_filter = (
                    Q(last_name__unaccent__icontains=search)
                    | Q(first_name__unaccent__icontains=search)
                    | Q(usage_name__unaccent__icontains=search)
                    | Q(user__first_name__unaccent__icontains=search)
                    | Q(user__usage_name__unaccent__icontains=search)
                    | Q(user__last_name__unaccent__icontains=search)
                    | Q(company_name__unaccent__icontains=search)
                )
                combined_filters = combined_filters & word_filter

            return self.filter(combined_filters)

        def with_status(
            self, status: str, at_datetime: datetime.datetime | datetime.date = None
        ):
            if at_datetime is None:
                at_datetime = timezone.now()

            at_datetime = ensure_datetime(at_datetime)

            share_owners_with_nb_of_shares = NumberOfSharesService.annotate_share_owner_queryset_with_nb_of_active_shares(
                ShareOwner.objects.all(), at_datetime.date()
            )
            members_without_shares = share_owners_with_nb_of_shares.filter(
                **{NumberOfSharesService.ANNOTATION_NUMBER_OF_ACTIVE_SHARES: 0}
            )

            if status == MemberStatus.SOLD:
                return self.filter(id__in=members_without_shares).distinct()

            members_with_valid_shares = self.exclude(id__in=members_without_shares)

            members_with_investing_annotation = InvestingStatusService.annotate_share_owner_queryset_with_investing_status_at_datetime(
                ShareOwner.objects.all(), at_datetime
            )
            investing_members = members_with_investing_annotation.filter(
                **{InvestingStatusService.ANNOTATION_WAS_INVESTING: True}
            )
            if status == MemberStatus.INVESTING:
                return members_with_valid_shares.filter(
                    id__in=investing_members
                ).distinct()

            member_with_shares_and_not_investing: Self = (
                members_with_valid_shares.exclude(id__in=investing_members)
            )

            members_with_paused_annotation = MembershipPauseService.annotate_share_owner_queryset_with_has_active_pause(
                ShareOwner.objects.all(), at_datetime.date()
            )
            paused_members = members_with_paused_annotation.filter(
                **{MembershipPauseService.ANNOTATION_HAS_ACTIVE_PAUSE: True}
            )

            if status == MemberStatus.PAUSED:
                return member_with_shares_and_not_investing.filter(
                    id__in=paused_members
                ).distinct()

            if status == MemberStatus.ACTIVE:
                return member_with_shares_and_not_investing.exclude(
                    id__in=paused_members
                ).distinct()

            raise TapirException(f"Invalid status : {status}")

        def with_fully_paid(self, fully_paid: bool):
            annotated = self.annotate(
                paid_amount=Sum("credited_payments__amount")
            ).annotate(
                expected_payments=Count("share_ownerships", distinct=True)
                * COOP_SHARE_PRICE
                + COOP_ENTRY_AMOUNT
            )
            if fully_paid:
                return annotated.filter(paid_amount__gte=F("expected_payments"))
            return annotated.filter(
                Q(paid_amount__lt=F("expected_payments")) | Q(paid_amount=None)
            )

    objects = ShareOwnerQuerySet.as_manager()

    def blank_info_fields(self):
        """Used after a ShareOwner is linked to a user, which is used as the source for user info instead."""
        self.first_name = ""
        self.last_name = ""
        self.usage_name = ""
        self.pronouns = ""
        self.email = ""
        self.birthdate = None
        self.street = ""
        self.street_2 = ""
        self.postcode = ""
        self.city = ""
        self.country = ""
        self.preferred_language = ""
        self.phone_number = ""

    def clean(self):
        r = super().clean()
        if self.is_company and self.user:
            raise ValidationError(_("Cannot be a company and have a Tapir account"))

        if self.user and (
            self.first_name
            or self.last_name
            or self.email
            or self.birthdate
            or self.street
            or self.street_2
            or self.postcode
            or self.city
            or self.country
            or self.preferred_language
            or self.phone_number
        ):
            raise ValidationError(
                _("User info should be stored in associated Tapir account")
            )
        return r

    def get_display_name(self, display_type):
        return UserUtils.build_display_name(self, display_type)

    def get_html_link(self, display_type):
        return get_html_link(
            url=self.get_absolute_url(), text=self.get_display_name(display_type)
        )

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def get_info(self):
        return self.user if self.user else self

    def get_absolute_url(self):
        if self.user:
            return self.user.get_absolute_url()
        return reverse("coop:shareowner_detail", args=[self.pk])

    def get_oldest_active_share_ownership(self):
        # This is equivalent to:
        # return self.get_active_share_ownerships().order_by("start_date").first()
        # but since using order_by will always trigger a database request, instead
        # we do the request manually. If the share_ownerships are already cached, we avoid a database request
        oldest = None
        for share_ownership in self.share_ownerships.all():
            if not share_ownership.is_active():
                continue

            if oldest is None or share_ownership.start_date < oldest.start_date:
                oldest = share_ownership
        return oldest

    def num_shares(self) -> int:
        return NumberOfSharesService.get_number_of_active_shares(self)

    def get_member_status(self, at_datetime: datetime.datetime | datetime.date = None):
        if not at_datetime:
            at_datetime = timezone.now()

        at_datetime = ensure_datetime(at_datetime)

        if (
            not NumberOfSharesService.get_number_of_active_shares(
                self, at_datetime.date()
            )
            > 0
        ):
            return MemberStatus.SOLD

        if InvestingStatusService.is_investing(self, at_datetime):
            return MemberStatus.INVESTING

        if MembershipPauseService.has_active_pause(self, at_datetime.date()):
            return MemberStatus.PAUSED

        return MemberStatus.ACTIVE

    def can_shop(self, at_datetime: datetime.datetime | datetime.date | None = None):
        return (
            self.user is not None
            and self.is_active(at_datetime)
            and ShiftCanShopService.can_shop(self, at_datetime)
        )

    def is_active(
        self, at_datetime: datetime.datetime | datetime.date | None = None
    ) -> bool:
        return self.get_member_status(at_datetime) == MemberStatus.ACTIVE

    def get_total_expected_payment(self) -> float:
        return COOP_ENTRY_AMOUNT + self.share_ownerships.count() * COOP_SHARE_PRICE

    def get_currently_paid_amount(self, at_date: datetime.date | None = None) -> float:
        if at_date is None:
            at_date = timezone.now().date()

        return (
            IncomingPayment.objects.filter(
                credited_member=self, payment_date__lte=at_date
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )

    def get_id_for_biooffice(self):
        return "299" + "{:0>9}".format(self.id)

    def get_member_number(self):
        return self.id

    def get_is_company(self):
        return self.is_company

    def get_membership_end_date(self):
        if self.get_member_status() == MemberStatus.SOLD:
            return None

        if not self.share_ownerships.exists():
            return None

        if self.share_ownerships.filter(end_date__isnull=True).exists():
            return None

        return self.share_ownerships.aggregate(Max("end_date"))["end_date__max"]

    def get_membership_start_date(self):
        if self.get_member_status() != MemberStatus.SOLD:
            return None

        if not self.share_ownerships.exists():
            return None

        shares_starting_in_the_future = self.share_ownerships.filter(
            start_date__gt=timezone.now().date()
        )
        if not shares_starting_in_the_future.exists():
            return None

        return shares_starting_in_the_future.aggregate(Min("start_date"))[
            "start_date__min"
        ]

    def __str__(self):
        return self.get_info().get_display_name(UserUtils.DISPLAY_NAME_TYPE_FULL)


class MemberStatus:
    SOLD = "sold"
    INVESTING = "investing"
    ACTIVE = "active"
    PAUSED = "paused"

    @classmethod
    def get_status_color(cls, status: str):
        # Should correspond to the standard bootstrap color classes
        match status:
            case cls.SOLD:
                return "danger"
            case cls.INVESTING:
                return "primary"
            case cls.ACTIVE:
                return "success"
            case cls.PAUSED:
                return "secondary"
            case _:
                raise TapirException(f"Unknown member status : {status}")


MEMBER_STATUS_CHOICES = (
    (MemberStatus.SOLD, _("Not a member")),
    (MemberStatus.INVESTING, _("Investing")),
    (MemberStatus.ACTIVE, _("Active")),
    (MemberStatus.PAUSED, _("Paused")),
)


def get_member_status_translation(searched_status: str) -> str:
    for status in MEMBER_STATUS_CHOICES:
        if searched_status == status[0]:
            return status[1]


class UpdateShareOwnerLogEntry(UpdateModelLogEntry):
    template_name = "coop/log/update_share_owner_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        share_owner: ShareOwner,
        actor: User,
    ):
        return super().populate_base(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            share_owner=share_owner,
            actor=actor,
        )


class ShareOwnership(DurationModelMixin, models.Model):
    """ShareOwnership represents ownership of a single share."""

    share_owner = models.ForeignKey(
        ShareOwner,
        related_name="share_ownerships",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    amount_paid = models.DecimalField(
        blank=False,
        null=False,
        default=COOP_SHARE_PRICE,
        max_digits=10,
        decimal_places=2,
    )

    def is_fully_paid(self):
        return self.amount_paid >= COOP_SHARE_PRICE

    def clean(self):
        super().clean()
        if self.amount_paid < 0:
            raise ValidationError(_("Amount paid for a share can't be negative"))
        if self.amount_paid > COOP_SHARE_PRICE:
            raise ValidationError(
                _(
                    f"Amount paid for a share can't more than {COOP_SHARE_PRICE} (the price of a share)"
                )
            )

    def __str__(self):
        return (
            f"{self.share_owner.get_display_name(display_type=UserUtils.DISPLAY_NAME_TYPE_FULL)} "
            f"from {self.start_date} to {self.end_date} (ID:{self.id})"
        )


class DeleteShareOwnershipLogEntry(ModelLogEntry):
    template_name = "coop/log/delete_share_ownership_log_entry.html"
    exclude_fields = ["id", "share_owner"]

    def populate(self, share_owner: ShareOwner, actor, model):
        return self.populate_base(share_owner=share_owner, actor=actor, model=model)


class DraftUser(models.Model):
    class MustSolveBeforeCreatingShareOwner:
        NO_EMAIL = "no_email"
        NO_FIRST_NAME = "no_first_name"
        NO_LAST_NAME = "no_last_name"
        MEMBERSHIP_AGREEMENT_NOT_SIGNED = "membership_agreement_not_signed"
        SHARE_COUNT_NOT_POSITIVE = "share_count_not_positive"
        SHARE_OWNER_ALREADY_CREATED = "share_owner_already_created"

    first_name = models.CharField(
        _("Administrative first name"), max_length=150, blank=True
    )
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    usage_name = models.CharField(
        _("Usage name"),
        max_length=150,
        blank=True,
        help_text=_(help_text_displayed_name),
    )
    pronouns = models.CharField(_("Pronouns"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone_number = PhoneNumberField(_("Phone number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
    )

    num_shares = models.IntegerField(_("Number of Shares"), blank=False, default=1)

    is_investing = models.BooleanField(
        verbose_name=_("Investing member"), default=False
    )

    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Entrance Fee"), default=False)
    paid_shares = models.BooleanField(_("Paid Shares"), default=False)

    ratenzahlung = models.BooleanField(verbose_name=_("Ratenzahlung"), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    share_owner = models.OneToOneField(
        ShareOwner,
        related_name="draft_user",
        null=True,
        on_delete=models.CASCADE,
    )

    def get_absolute_url(self):
        return reverse("coop:draftuser_detail", args=[self.pk])

    def get_initial_amount(self):
        return self.num_shares * COOP_SHARE_PRICE + COOP_ENTRY_AMOUNT

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def can_create_user(self):
        return len(self.must_solve_before_creating_share_owner()) == 0

    def must_solve_before_creating_share_owner(self):
        to_solve = []

        if not self.email:
            to_solve.append(self.MustSolveBeforeCreatingShareOwner.NO_EMAIL)
        if not self.first_name:
            to_solve.append(self.MustSolveBeforeCreatingShareOwner.NO_FIRST_NAME)
        if not self.last_name:
            to_solve.append(self.MustSolveBeforeCreatingShareOwner.NO_LAST_NAME)
        if not self.signed_membership_agreement:
            to_solve.append(
                self.MustSolveBeforeCreatingShareOwner.MEMBERSHIP_AGREEMENT_NOT_SIGNED
            )
        if not self.num_shares > 0:
            to_solve.append(
                self.MustSolveBeforeCreatingShareOwner.SHARE_COUNT_NOT_POSITIVE
            )
        if self.share_owner:
            to_solve.append(
                self.MustSolveBeforeCreatingShareOwner.SHARE_OWNER_ALREADY_CREATED
            )

        return to_solve

    def must_solve_before_creating_share_owner_display(self):
        result = ""
        for to_solve in self.must_solve_before_creating_share_owner():
            if result != "":
                result += "<br />"
            match to_solve:
                case self.MustSolveBeforeCreatingShareOwner.NO_EMAIL:
                    message = _("Email address must be set.")
                case self.MustSolveBeforeCreatingShareOwner.NO_FIRST_NAME:
                    message = _("First name must be set.")
                case self.MustSolveBeforeCreatingShareOwner.NO_LAST_NAME:
                    message = _("Last name must be set.")
                case (
                    self.MustSolveBeforeCreatingShareOwner.MEMBERSHIP_AGREEMENT_NOT_SIGNED
                ):
                    message = _("Membership agreement must be signed.")
                case self.MustSolveBeforeCreatingShareOwner.SHARE_COUNT_NOT_POSITIVE:
                    message = _("Amount of requested shares must be positive.")
                case self.MustSolveBeforeCreatingShareOwner.SHARE_OWNER_ALREADY_CREATED:
                    message = _("Member already created.")
                case _:
                    raise TapirException(
                        f"Unknown MustSolveBeforeCreatingShareOwner value : {to_solve}"
                    )
            result += message
        return result

    def get_info(self):
        """
        get_info is an interface implemented by both ShareOwner and DraftUser
        to allow identical treatment in templates.
        """
        return self.share_owner.get_info() if self.share_owner else self

    @staticmethod
    def get_member_number():
        return None

    @staticmethod
    def get_is_company():
        return False


class IncomingPayment(models.Model):
    paying_member = models.ForeignKey(
        ShareOwner,
        verbose_name=_("Paying member"),
        related_name="debited_payments",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    credited_member = models.ForeignKey(
        ShareOwner,
        verbose_name=_("Credited member"),
        related_name="credited_payments",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    amount = models.FloatField(
        verbose_name=_("Amount"),
        null=False,
        blank=False,
        validators=[positive_number_validator],
    )
    payment_date = models.DateField(
        verbose_name=_("Payment date"), null=False, blank=False
    )
    creation_date = models.DateField(
        verbose_name=_("Creation date"), null=False, blank=False
    )
    comment = models.TextField(blank=True, null=False, default="")
    created_by = models.ForeignKey(
        TapirUser,
        verbose_name=_("Created by"),
        related_name="creator",
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )


class CreatePaymentLogEntry(LogEntry):
    amount = models.FloatField(blank=False, null=False)
    payment_date = models.DateField(null=False, blank=False)

    template_name = "coop/log/create_payment_log_entry.html"

    def populate(
        self,
        actor: User,
        share_owner: ShareOwner,
        amount: float,
        payment_date: datetime.date,
    ):
        self.amount = amount
        self.payment_date = payment_date
        return super().populate_base(actor=actor, share_owner=share_owner)


class UpdateIncomingPaymentLogEntry(UpdateModelLogEntry):
    template_name = "coop/log/update_incoming_payment_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        share_owner: ShareOwner,
        actor: User,
    ):
        return super().populate_base(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            share_owner=share_owner,
            actor=actor,
        )


class DeleteIncomingPaymentLogEntry(ModelLogEntry):
    template_name = "coop/log/delete_incoming_payment_log_entry.html"
    exclude_fields = ["id", "credited_member", "paying_member", "comment", "created_by"]

    def populate(self, share_owner: ShareOwner, actor, model):
        return self.populate_base(share_owner=share_owner, actor=actor, model=model)


class CreateShareOwnershipsLogEntry(LogEntry):
    num_shares = PositiveIntegerField(blank=False, null=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    template_name = "coop/log/create_share_ownerships_log_entry.html"

    def populate(
        self,
        actor,
        share_owner,
        num_shares: int,
        start_date: datetime.date,
        end_date: datetime.date | None,
    ):
        self.num_shares = num_shares
        self.start_date = start_date
        self.end_date = end_date
        return super().populate_base(actor=actor, share_owner=share_owner)


class UpdateShareOwnershipLogEntry(UpdateModelLogEntry):
    share_ownership_id = PositiveIntegerField(blank=False, null=False)

    template_name = "coop/log/update_share_ownership_log_entry.html"

    def populate(
        self,
        share_ownership: ShareOwnership,
        old_frozen: dict,
        new_frozen: dict,
        actor,
        share_owner: ShareOwner,
    ):
        self.share_ownership_id = share_ownership.id
        return super().populate_base(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            actor=actor,
            share_owner=share_owner,
        )


class NewMembershipsForAccountingRecap(models.Model):
    member = models.ForeignKey(
        ShareOwner,
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    number_of_shares = models.PositiveIntegerField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)


class ExtraSharesForAccountingRecap(models.Model):
    member = models.ForeignKey(
        ShareOwner,
        null=False,
        blank=False,
        on_delete=models.deletion.PROTECT,
    )
    number_of_shares = models.PositiveIntegerField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)


class MembershipPause(DurationModelMixin, models.Model):
    class Meta:
        indexes = [models.Index(fields=["share_owner"])]

    share_owner = models.ForeignKey(
        ShareOwner, on_delete=models.deletion.CASCADE, verbose_name=_("Member")
    )
    description = models.CharField(max_length=1000)


class MembershipPauseCreatedLogEntry(ModelLogEntry):
    template_name = "coop/log/create_membership_pause_log_entry.html"

    def populate(
        self,
        actor: User,
        pause: MembershipPause,
    ):
        return super().populate_base(
            actor=actor, share_owner=pause.share_owner, model=pause
        )

    def get_context_data(self):
        context_data = super().get_context_data()
        context_data["start_date"] = datetime.datetime.strptime(
            self.values["start_date"], "%Y-%m-%d"
        ).date()
        return context_data

    def render(self):
        print(self.values)
        return super().render()


class MembershipPauseUpdatedLogEntry(UpdateModelLogEntry):
    template_name = "coop/log/update_membership_pause_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        pause: MembershipPause,
        actor: User,
    ):
        return super().populate_base(
            actor=actor,
            share_owner=pause.share_owner,
            old_frozen=old_frozen,
            new_frozen=new_frozen,
        )


class MembershipResignation(models.Model):
    class ResignationType(models.TextChoices):
        BUY_BACK = "coop_buys_shares_back", _(
            "The cooperative buys the shares back from the member"
        )
        GIFT_TO_COOP = "gift_to_coop", _(
            "The member gifts the shares to the cooperative"
        )
        TRANSFER = "transfer", _("The shares get transferred to another member")

    share_owner = models.OneToOneField(
        ShareOwner,
        on_delete=models.deletion.CASCADE,
        verbose_name=_("Shareowner"),
        related_name="share_owner",
    )
    cancellation_date = models.DateField(
        default=timezone.now,
    )
    pay_out_day = models.DateField(null=True)
    cancellation_reason = models.CharField(max_length=1000)
    resignation_type = models.CharField(choices=ResignationType.choices, max_length=50)
    transferring_shares_to = models.OneToOneField(
        ShareOwner,
        on_delete=models.deletion.PROTECT,
        verbose_name="OwnerToTransfer",
        null=True,
        related_name="owner_to_transfer",
        help_text=_(
            "Leave this empty if the resignation type is not a transfer to another member"
        ),
    )
    paid_out = models.BooleanField(default=False)

    class MembershipResignationQuerySet(models.QuerySet):
        def with_name_or_id(self, search_string: str):
            id_filter = Q(share_owner__id=search_string)
            member_filter = Q(
                share_owner__in=ShareOwner.objects.with_name(search_string)
            )
            combined_filters = id_filter | member_filter
            return self.filter(combined_filters)

    objects = MembershipResignationQuerySet.as_manager()


class MembershipResignationCreateLogEntry(ModelLogEntry):
    template_name = "coop/log/create_resignmember_log_entry.html"

    def populate(
        self,
        actor: User,
        model: MembershipResignation,
    ):
        return super().populate_base(
            actor=actor, share_owner=model.share_owner, model=model
        )


class MembershipResignationUpdateLogEntry(UpdateModelLogEntry):
    template_name = "coop/log/update_resignmember_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        model: MembershipResignation,
        actor: User,
    ):
        return super().populate_base(
            actor=actor,
            share_owner=model.share_owner,
            old_frozen=old_frozen,
            new_frozen=new_frozen,
        )
