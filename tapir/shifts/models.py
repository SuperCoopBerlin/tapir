from __future__ import annotations

import calendar
import datetime

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser
from tapir.log.models import ModelLogEntry, UpdateModelLogEntry, LogEntry
from tapir.utils.models import DurationModelMixin
from tapir.utils.shortcuts import get_html_link, get_timezone_aware_datetime, get_monday


class ShiftUserCapability:
    SHIFT_COORDINATOR = "shift_coordinator"
    CASHIER = "cashier"
    MEMBER_OFFICE = "member_office"
    BREAD_DELIVERY = "bread_delivery"
    RED_CARD = "red_card"
    FIRST_AID = "first_aid"
    WELCOME_SESSION = "welcome_session"
    HANDLING_CHEESE = "handling_cheese"
    TRAIN_CHEESE_HANDLERS = "train_cheese_handlers"
    INVENTORY = "inventory"
    NEBENAN_DE_SUPPORT = "nebenan_de_support"


SHIFT_USER_CAPABILITY_CHOICES = {
    ShiftUserCapability.SHIFT_COORDINATOR: _("Teamleader"),
    ShiftUserCapability.CASHIER: _("Cashier"),
    ShiftUserCapability.MEMBER_OFFICE: _("Member Office"),
    ShiftUserCapability.BREAD_DELIVERY: _("Bread Delivery"),
    ShiftUserCapability.RED_CARD: _("Red Card"),
    ShiftUserCapability.FIRST_AID: _("First Aid"),
    ShiftUserCapability.WELCOME_SESSION: _("Welcome Session"),
    ShiftUserCapability.HANDLING_CHEESE: _("Handling Cheese"),
    ShiftUserCapability.TRAIN_CHEESE_HANDLERS: _("Train cheese handlers"),
    ShiftUserCapability.INVENTORY: _("Inventory"),
    ShiftUserCapability.NEBENAN_DE_SUPPORT: _("Nebenan.de-Support"),
}


class ShiftSlotWarning:
    IN_THE_MORNING_EVERYONE_HELPS_STORAGE = "in_the_morning_everyone_helps_storage"
    IN_THE_EVENING_EVERYONE_HELPS_CLEAN = "in_the_evening_everyone_helps_clean"
    BREAD_PICKUP_NEEDS_A_VEHICLE = "bread_picked_needs_a_vehicle"
    MUST_BE_ABLE_TO_CARRY_HEAVY_WEIGHTS = "must_be_able_to_carry_heavy_weights"
    MUST_NOT_BE_SCARED_OF_HEIGHTS = "must_not_be_scared_of_heights"


SHIFT_SLOT_WARNING_CHOICES = {
    ShiftSlotWarning.IN_THE_MORNING_EVERYONE_HELPS_STORAGE: _(
        "I understand that all working groups help the Warenannahme & Lager working group until the shop opens."
    ),
    ShiftSlotWarning.IN_THE_EVENING_EVERYONE_HELPS_CLEAN: _(
        "I understand that all working groups help the Reinigung & Aufräumen working group after the shop closes."
    ),
    ShiftSlotWarning.BREAD_PICKUP_NEEDS_A_VEHICLE: _(
        "I understand that I need my own vehicle in order to pick up the bread. A cargo bike can be borrowed, more infos in Slack in the #cargobike channel"
    ),
    ShiftSlotWarning.MUST_BE_ABLE_TO_CARRY_HEAVY_WEIGHTS: _(
        "I understand that I may need to carry heavy weights for this shift."
    ),
    ShiftSlotWarning.MUST_NOT_BE_SCARED_OF_HEIGHTS: _(
        "I understand that I may need to work high, for example up a ladder. I do not suffer from fear of heights."
    ),
}


class ShiftNames:
    NAME_INT_PAIRS = [
        {"name": "A", "index": 0},
        {"name": "B", "index": 1},
        {"name": "C", "index": 2},
        {"name": "D", "index": 3},
    ]

    @staticmethod
    def get_name(index: int) -> str | None:
        for pair in ShiftNames.NAME_INT_PAIRS:
            if pair["index"] == index:
                return pair["name"]
        return None

    @staticmethod
    def get_index(name: str) -> int | None:
        for pair in ShiftNames.NAME_INT_PAIRS:
            if pair["name"] == name:
                return pair["index"]
        return None


class ShiftTemplateGroup(models.Model):
    """ShiftTemplateGroup represents a collection of ShiftTemplates that are usually instantiated together.

    Normally, this will be a week of shifts in the ABCD system, so one ShiftTemplateGroup might be "Week A".
    """

    name = models.CharField(blank=False, max_length=255)
    NAME_INT_PAIRS = [
        {"name": "A", "index": 0},
        {"name": "B", "index": 1},
        {"name": "C", "index": 2},
        {"name": "D", "index": 3},
    ]

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name}"

    def create_shifts(self, start_date: datetime.date):
        if start_date.weekday() != 0:
            raise ValueError("Start date for shift generation must be a Monday")
        start_date_in_the_past_or_null = Q(start_date__lte=start_date) | Q(
            start_date__isnull=True
        )
        return [
            shift_template.create_shift(start_date=start_date)
            for shift_template in self.shift_templates.filter(
                start_date_in_the_past_or_null
            )
        ]

    def get_group_index(self) -> int | None:
        for pair in ShiftTemplateGroup.NAME_INT_PAIRS:
            if pair["name"] == self.name:
                return pair["index"]
        return None

    @staticmethod
    def get_group_from_index(index: int) -> ShiftTemplateGroup | None:
        for pair in ShiftTemplateGroup.NAME_INT_PAIRS:
            if pair["index"] == index:
                return ShiftTemplateGroup.objects.get(name=pair["name"])
        return None


# Generate weekdays
WEEKDAY_CHOICES = [
    (i, _(calendar.day_name[i])) for i in calendar.Calendar().iterweekdays()
]


class ShiftTemplate(models.Model):
    """ShiftTemplate represents a (usually recurring) shift that may be instantiated as a concrete Shift.

    Usually, a ShiftTemplate will be part of a ShiftTemplateGroup, such as "Week A". ShiftTemlates has an associated
    weekday. So "Week A" may have a ShiftTemplate for Tuesday 9:00 - 12:00. When instantiating the ShiftTemplateGroup,
    a Shift will be created on Tuesday of the selected week.

    ShiftTemplates also have ShiftAttendanceTemplates associated with them that represent regularly-occurring shift
    placements of workers. For example, John might work every shift in Week A on Tue 9:00 - 12:00. Every time a Shift
    is instantiated from the ShiftTemplate, a ShiftAttendance is automatically created to track John's attendance.

    When ShiftAttendanceTemplates change, ShiftAttendances of already-generated future shifts are automatically updated
    with the members that have joined or left the ShiftTemplate. This is because Shifts are usually generated for a year
    in advance but memberships in the work squads change throughout the year."""

    name = models.CharField(blank=False, max_length=255)
    description = models.TextField(blank=True, null=False, default="")
    group = models.ForeignKey(
        ShiftTemplateGroup,
        related_name="shift_templates",
        null=True,
        on_delete=models.PROTECT,
    )
    num_required_attendances = models.PositiveIntegerField(
        null=False, blank=False, default=3
    )
    weekday = models.IntegerField(blank=True, null=True, choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(blank=False)
    end_time = models.TimeField(blank=False)
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text=_(
            "This determines from which date shifts should be generated from this ABCD shift."
        ),
    )

    def __str__(self):
        display_name = "%s: %s %s %s-%s" % (
            self.__class__.__name__,
            self.name,
            self.get_weekday_display(),
            self.start_time.strftime("%H:%M"),
            self.end_time.strftime("%H:%M"),
        )
        if self.group:
            display_name = f"{display_name} ({self.group.name})"
        return display_name

    def get_absolute_url(self):
        return reverse("shifts:shift_template_detail", args=[self.pk])

    def get_attendance_templates(self):
        return ShiftAttendanceTemplate.objects.filter(
            slot_template__in=self.slot_templates.all()
        )

    def get_future_generated_shifts(self, now=None):
        return self.generated_shifts.filter(
            start_time__gt=now or timezone.now()
        ).order_by("start_time")

    def get_past_generated_shifts(self, now=None):
        return self.generated_shifts.filter(
            start_time__lte=now or timezone.now()
        ).order_by("-start_time")

    def get_display_name(self):
        display_name = "%s %s %s" % (
            self.name,
            _(self.get_weekday_display()),
            self.start_time.strftime("%H:%M"),
        )
        if self.group:
            display_name = f"{display_name} ({self.group.name})"
        return display_name

    def _generate_shift(self, start_date: datetime.date):
        shift_date = start_date
        # If this is a shift that is not part of a group and just gets placed manually, just use the day selected
        if self.weekday:
            while True:
                if shift_date.weekday() == self.weekday:
                    break
                shift_date += datetime.timedelta(days=1)

        start_time = get_timezone_aware_datetime(shift_date, self.start_time)
        end_time = get_timezone_aware_datetime(shift_date, self.end_time)

        return Shift(
            shift_template=self,
            name=self.name,
            start_time=start_time,
            end_time=end_time,
            description=self.description,
            num_required_attendances=self.num_required_attendances,
        )

    @transaction.atomic
    def create_shift(self, start_date: datetime.date) -> Shift:
        generated_shift = self._generate_shift(start_date=start_date)
        shift = self.generated_shifts.filter(
            start_time=generated_shift.start_time
        ).first()

        if shift:
            return shift

        generated_shift.save()
        shift = generated_shift

        for slot_template in self.slot_templates.all():
            slot = slot_template.create_slot_from_template(shift)
            slot.update_attendance_from_template()

        return shift

    def update_future_shift_attendances(self, now=None):
        for slot_template in self.slot_templates.all():
            slot_template.update_future_slot_attendances(now)

    def add_slot_template_and_update_future_shifts(
        self, slot_name: str, required_capabilities: []
    ):
        slot_template = ShiftSlotTemplate.objects.create(
            name=slot_name,
            shift_template=self,
            required_capabilities=required_capabilities,
        )
        for shift in self.generated_shifts.filter(start_time__gt=timezone.now()):
            slot_template.create_slot_from_template(shift)

    def update_future_generated_shifts_to_fit_this(self):
        with transaction.atomic():
            for shift in self.get_future_generated_shifts():
                shift.update_to_fit_template()

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(
                f"The shift must end after it starts. Given start time: {self.start_time}. Given end time: {self.end_time}"
            )


class RequiredCapabilitiesMixin:
    # Théo 23.12.22 the required_capabilities field could be moved to this class, but we'd need to migrate
    # the data from ShiftSlot and ShiftSlotTemplate to it first
    def get_required_capabilities_display(self):
        return ", ".join(
            [
                str(SHIFT_USER_CAPABILITY_CHOICES[capability])
                for capability in self.required_capabilities
            ]
        )

    def get_required_capabilities_dict(self):
        """
        returns required capabilites as dictionary with corresponding translatiom
        """
        return {
            capability: _(SHIFT_USER_CAPABILITY_CHOICES[capability])
            for capability in self.required_capabilities
        }


class ShiftSlotTemplate(RequiredCapabilitiesMixin, models.Model):
    name = models.CharField(blank=True, max_length=255)
    shift_template = models.ForeignKey(
        ShiftTemplate,
        related_name="slot_templates",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    required_capabilities = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_USER_CAPABILITY_CHOICES.items(), blank=False
        ),
        default=list,
        blank=True,
        null=False,
    )

    warnings = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_SLOT_WARNING_CHOICES.items(), blank=False
        ),
        default=list,
        blank=True,
        null=False,
    )

    def get_display_name(self):
        display_name = self.shift_template.get_display_name()
        if self.name:
            display_name = "{} {}".format(self.name, display_name)
        return display_name

    def user_can_attend(self, user):
        return (
            # Slot must not be attended yet
            not hasattr(self, "attendance_template")
            and
            # User isn't already registered for this shift
            not self.shift_template.get_attendance_templates()
            .filter(user=user)
            .exists()
            and
            # User must have all required capabilities
            set(self.required_capabilities).issubset(user.shift_user_data.capabilities)
        )

    def get_attendance_template(self):
        return (
            self.attendance_template if hasattr(self, "attendance_template") else None
        )

    def update_future_slot_attendances(self, now=None):
        for slot in self.generated_slots.filter(
            shift__start_time__gt=now or timezone.now()
        ):
            slot.update_attendance_from_template()

    def create_slot_from_template(self, shift: Shift):
        return ShiftSlot.objects.create(
            slot_template=self,
            name=self.name,
            shift=shift,
            required_capabilities=self.required_capabilities,
            warnings=self.warnings,
        )


class ShiftAttendanceTemplate(models.Model):
    user = models.ForeignKey(
        TapirUser, related_name="shift_attendance_templates", on_delete=models.PROTECT
    )
    slot_template = models.OneToOneField(
        ShiftSlotTemplate, related_name="attendance_template", on_delete=models.PROTECT
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.slot_template.update_future_slot_attendances()

    def cancel_attendances(self, starting_from: datetime.datetime):
        for attendance in ShiftAttendance.objects.filter(
            slot__in=self.slot_template.generated_slots.all(),
            user=self.user,
            slot__shift__start_time__gte=starting_from,
        ):
            attendance.state = ShiftAttendance.State.CANCELLED
            attendance.save()


class ShiftAttendanceTemplateLogEntry(ModelLogEntry):
    class Meta:
        abstract = True

    exclude_fields = ["slot_template"]

    # Don't link directly to the slot because it may be less stable than the shift
    slot_template_name = models.CharField(blank=True, max_length=255)
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.PROTECT)

    def populate(
        self,
        actor: User,
        tapir_user: TapirUser,
        shift_attendance_template: ShiftAttendanceTemplate,
    ):
        self.slot_template_name = shift_attendance_template.slot_template.name
        self.shift_template = shift_attendance_template.slot_template.shift_template
        return super().populate_base(
            actor=actor, tapir_user=tapir_user, model=shift_attendance_template
        )


class CreateShiftAttendanceTemplateLogEntry(ShiftAttendanceTemplateLogEntry):
    template_name = "shifts/log/create_shift_attendance_template_log_entry.html"


class DeleteShiftAttendanceTemplateLogEntry(ShiftAttendanceTemplateLogEntry):
    template_name = "shifts/log/delete_shift_attendance_template_log_entry.html"


class Shift(models.Model):
    # ShiftTemplate that this shift was generated from, may be null for manually-created shifts
    shift_template = models.ForeignKey(
        ShiftTemplate,
        null=True,
        blank=True,
        related_name="generated_shifts",
        on_delete=models.PROTECT,
    )

    name = models.CharField(blank=False, max_length=255)
    num_required_attendances = models.PositiveIntegerField(
        verbose_name=_("Number of required attendances"),
        help_text=_(
            "If there are less members registered to a shift than that number, "
            "it will be highlighted in the shift calendar."
        ),
        null=True,
        blank=False,
        default=3,
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Is shown on the shift page below the title"),
        blank=True,
        null=False,
        default="",
    )

    start_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)

    cancelled = models.BooleanField(default=False)
    cancelled_reason = models.CharField(null=True, max_length=1000)

    NB_DAYS_FOR_SELF_UNREGISTER = 7
    NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN = 2

    def __str__(self):
        display_name = "%s: %s %s-%s" % (
            self.__class__.__name__,
            self.name,
            timezone.localtime(self.start_time).strftime("%a %Y-%m-%d %H:%M"),
            timezone.localtime(self.end_time).strftime("%H:%M"),
        )
        if self.shift_template and self.shift_template.group:
            display_name = f"{display_name} ({self.shift_template.group.name})"

        display_name = "%s [%d/%d]" % (
            display_name,
            self.get_valid_attendances().count(),
            self.slots.count(),
        )

        return display_name

    def get_display_name(self):
        display_name = "%s %s - %s" % (
            self.name,
            timezone.localtime(self.start_time).strftime("%a, %d %b %Y %H:%M"),
            timezone.localtime(self.end_time).strftime("%H:%M"),
        )
        if self.shift_template and self.shift_template.group:
            display_name = f"{display_name} ({self.shift_template.group.name})"
        return display_name

    def get_absolute_url(self):
        return reverse("shifts:shift_detail", args=[self.pk])

    def get_attendances(self) -> ShiftAttendance.ShiftAttendanceQuerySet:
        return ShiftAttendance.objects.filter(slot__shift=self)

    def get_valid_attendances(self) -> ShiftAttendance.ShiftAttendanceQuerySet:
        return self.get_attendances().with_valid_state()

    def is_in_the_future(self) -> bool:
        return self.start_time > timezone.now()

    def get_num_required_attendances(self) -> int:
        if self.shift_template:
            return self.shift_template.num_required_attendances
        return self.num_required_attendances

    def update_to_fit_template(self):
        date = get_monday(self.start_time.date()) + datetime.timedelta(
            days=self.shift_template.weekday
        )
        self.start_time = get_timezone_aware_datetime(
            date, self.shift_template.start_time
        )
        self.end_time = get_timezone_aware_datetime(date, self.shift_template.end_time)
        self.name = self.shift_template.name
        self.description = self.shift_template.description
        self.num_required_attendances = self.shift_template.num_required_attendances
        self.save()


class ShiftAttendanceLogEntry(ModelLogEntry):
    class Meta:
        abstract = True

    exclude_fields = ["slot"]

    slot_name = models.CharField(blank=True, max_length=255)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    state = models.IntegerField(null=True)

    def get_context_data(self):
        context = super().get_context_data()
        if self.state is not None:
            context["state_name"] = SHIFT_ATTENDANCE_STATES[self.state]
        return context

    def populate(self, actor: User, tapir_user: TapirUser, attendance: ShiftAttendance):
        self.slot_name = attendance.slot.name
        self.shift = attendance.slot.shift
        self.state = attendance.state
        return super().populate_base(
            actor=actor, tapir_user=tapir_user, model=attendance
        )


class CreateShiftAttendanceLogEntry(ShiftAttendanceLogEntry):
    template_name = "shifts/log/create_shift_attendance_log_entry.html"


class ShiftAttendanceTakenOverLogEntry(ShiftAttendanceLogEntry):
    template_name = "shifts/log/shift_attendance_taken_over_log_entry.html"


class ShiftSlot(RequiredCapabilitiesMixin, models.Model):
    slot_template = models.ForeignKey(
        ShiftSlotTemplate,
        null=True,
        blank=True,
        related_name="generated_slots",
        on_delete=models.PROTECT,
    )

    name = models.CharField(blank=True, max_length=255)
    shift = models.ForeignKey(
        Shift, related_name="slots", null=False, blank=False, on_delete=models.CASCADE
    )

    required_capabilities = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_USER_CAPABILITY_CHOICES.items(), blank=False
        ),
        default=list,
        blank=True,
        null=False,
    )

    warnings = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_SLOT_WARNING_CHOICES.items(), blank=False
        ),
        default=list,
        blank=True,
        null=False,
    )

    def get_display_name(self):
        display_name = self.shift.get_display_name()
        if self.name:
            display_name = "{} {}".format(self.name, display_name)
        return display_name

    def get_html_link(self):
        return get_html_link(self.shift.get_absolute_url(), self.get_display_name())

    def get_valid_attendance(self) -> ShiftAttendance:
        return self.attendances.with_valid_state().first()

    def user_can_attend(self, user):
        return (
            # Slot must not be attended yet
            (
                not self.get_valid_attendance()
                or self.get_valid_attendance().state
                == ShiftAttendance.State.LOOKING_FOR_STAND_IN
            )
            and
            # User isn't already registered for this shift
            not self.shift.get_attendances()
            .filter(user=user)
            .with_valid_state()
            .exists()
            and
            # User must have all required capabilities
            set(self.required_capabilities).issubset(user.shift_user_data.capabilities)
            and self.shift.is_in_the_future()
            and not self.shift.cancelled
        )

    def user_can_self_unregister(self, user: TapirUser) -> bool:
        user_is_registered_to_slot = (
            self.get_valid_attendance() is not None
            and self.get_valid_attendance().user == user
        )
        user_is_not_registered_to_slot_template = (
            self.slot_template is None
            or not ShiftAttendanceTemplate.objects.filter(
                slot_template=self.slot_template, user=user
            ).exists()
        )
        early_enough = (
            self.shift.start_time.date() - timezone.now().date()
        ).days >= Shift.NB_DAYS_FOR_SELF_UNREGISTER
        return (
            user_is_registered_to_slot
            and user_is_not_registered_to_slot_template
            and early_enough
        )

    def user_can_look_for_standin(self, user: TapirUser) -> bool:
        user_is_registered_to_slot = (
            self.get_valid_attendance() is not None
            and self.get_valid_attendance().user == user
        )
        early_enough = (
            self.shift.start_time - timezone.now()
        ).days >= Shift.NB_DAYS_FOR_SELF_LOOK_FOR_STAND_IN
        return user_is_registered_to_slot and early_enough

    def update_attendance_from_template(self):
        """Updates the attendance of this slot.

        This is used so that when people join a regularly-occurring ShiftSlot, future shifts already
        generated can be updated to reflect this change.

        For users leaving, the update has to be done in the view, as we can't know whether the user currently attending
        the slot just unregistered from the regular slot or wants to attend this slot one-time only.
        """

        if not self.slot_template:
            return

        attendance_template = self.slot_template.get_attendance_template()
        if (
            not attendance_template
            or self.get_valid_attendance()
            or attendance_template.user.shift_user_data.is_currently_exempted_from_shifts(
                self.shift.start_time.date()
            )
        ):
            return

        attendance = self.attendances.filter(user=attendance_template.user).first()
        if attendance is None:
            attendance = ShiftAttendance.objects.create(
                user=attendance_template.user, slot=self
            )
        attendance.state = ShiftAttendance.State.PENDING
        attendance.save()

    def update_slot_from_template(self):
        self.name = self.slot_template.name
        self.required_capabilities = self.slot_template.required_capabilities
        self.warnings = self.slot_template.warnings
        self.save()


class ShiftAccountEntry(models.Model):
    """ShiftAccountEntry represents and entry to the shift "bank account" of a user.

    Usually, a user will be debited one credit every four weeks and will be credited one for completing their shift.

    Based on the account balance and the dates of the entries, the penalties are calculated. For example, if the
    balance has been -2 for four weeks (TBD, this is just an example), the cooperator's right to shop will be revoked.
    """

    user = models.ForeignKey(
        TapirUser, related_name="shift_account_entries", on_delete=models.PROTECT
    )

    # Value of the transaction, may be negative (for example for missed shifts)
    value = models.IntegerField(blank=False)
    # Date the transaction is debited, credited
    date = models.DateTimeField(blank=False)
    description = models.CharField(blank=True, max_length=255)
    is_from_welcome_session = models.BooleanField(
        blank=False, null=False, default=False
    )


class ShiftAttendance(models.Model):
    class Meta:
        ordering = ["slot__shift__start_time"]
        indexes = [models.Index(fields=["slot"]), models.Index(fields=["state"])]

    class ShiftAttendanceQuerySet(models.QuerySet):
        def with_valid_state(self):
            return self.filter(state__in=ShiftAttendance.VALID_STATES)

    objects = ShiftAttendanceQuerySet.as_manager()

    user = models.ForeignKey(
        TapirUser, related_name="shift_attendances", on_delete=models.PROTECT
    )
    slot = models.ForeignKey(
        ShiftSlot, related_name="attendances", on_delete=models.PROTECT
    )
    reminder_email_sent = models.BooleanField(default=False)

    class State(models.IntegerChoices):
        PENDING = 1
        DONE = 2
        CANCELLED = 3
        MISSED = 4
        MISSED_EXCUSED = 5
        LOOKING_FOR_STAND_IN = 6

    VALID_STATES = [
        State.PENDING,
        State.DONE,
        State.LOOKING_FOR_STAND_IN,
    ]

    STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP = [
        State.PENDING,
        State.LOOKING_FOR_STAND_IN,
    ]

    state = models.IntegerField(choices=State.choices, default=State.PENDING)

    # Only filled if state is MISSED_EXCUSED
    excused_reason = models.TextField(blank=True)
    last_state_update = models.DateTimeField(null=True)

    account_entry = models.OneToOneField(
        ShiftAccountEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shift_attendance",
    )

    def get_state_display(self):
        return SHIFT_ATTENDANCE_STATES[self.state]

    def is_valid(self):
        return self.state in ShiftAttendance.VALID_STATES

    def get_absolute_url(self):
        return reverse(
            "shifts:update_shift_attendance_state_with_form", args=[self.pk, self.state]
        )

    # helper function for less boilerplate in serialization
    def get_shift(self):
        return self.slot.shift

    def update_shift_account_entry(self, entry_description=""):
        if self.account_entry is not None:
            previous_entry = self.account_entry
            self.account_entry = None
            self.save()
            previous_entry.delete()

        entry_value = None
        if self.state == ShiftAttendance.State.MISSED:
            entry_value = -1
        elif self.state in [
            ShiftAttendance.State.DONE,
            ShiftAttendance.State.MISSED_EXCUSED,
        ]:
            entry_value = 1

        if entry_value is None:
            return

        description = f"Shift {SHIFT_ATTENDANCE_STATES[self.state]} {self.slot.get_display_name()} {entry_description}"

        entry = ShiftAccountEntry.objects.create(
            user=self.user,
            value=entry_value,
            date=timezone.now(),
            description=description,
        )
        self.account_entry = entry
        self.save()


@receiver(pre_save, sender=ShiftAttendance)
def on_change(sender, instance: ShiftAttendance, **kwargs):
    if instance.id is None:
        instance.last_state_update = timezone.now()
        return

    previous = sender.objects.get(id=instance.id)
    if previous.state is instance.state:
        return

    instance.last_state_update = timezone.now()


SHIFT_ATTENDANCE_STATES = {
    ShiftAttendance.State.PENDING: _("Pending"),
    ShiftAttendance.State.DONE: _("Attended"),
    ShiftAttendance.State.MISSED: _("Missed"),
    ShiftAttendance.State.MISSED_EXCUSED: _("Excused"),
    ShiftAttendance.State.CANCELLED: _("Cancelled"),
    ShiftAttendance.State.LOOKING_FOR_STAND_IN: _("Looking for a stand-in"),
}


class UpdateShiftAttendanceStateLogEntry(ShiftAttendanceLogEntry):
    template_name = "shifts/log/update_shift_attendance_state_log_entry.html"


class UpdateShiftUserDataLogEntry(UpdateModelLogEntry):
    template_name = "shifts/log/update_shift_user_data_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        tapir_user: TapirUser,
        actor: User | None,
    ):
        return super().populate_base(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            tapir_user=tapir_user,
            actor=actor,
        )


class ShiftAttendanceMode:
    REGULAR = "regular"
    FLYING = "flying"
    FROZEN = "frozen"


class ShiftUserDataQuerySet(models.QuerySet):
    def is_covered_by_exemption(self, date=None):
        return self.filter(
            shift_exemptions__in=ShiftExemption.objects.active_temporal(date)
        )


class ShiftUserData(models.Model):
    # We create a ShiftUserData for every TapirUser with the Django Signals mechanism (see create_shift_user_data
    # below). For this reason, we assume TapirUser.shift_user_data to exist in all places in the code. Note that
    # signals do not get triggered by loaddata, so test fixtures need to include ShiftUserData.
    user = models.OneToOneField(
        TapirUser, null=False, on_delete=models.PROTECT, related_name="shift_user_data"
    )

    capabilities = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_USER_CAPABILITY_CHOICES.items(), blank=False
        ),
        default=list,
    )

    SHIFT_ATTENDANCE_MODE_CHOICES = [
        (ShiftAttendanceMode.REGULAR, _("🏠 ABCD")),
        (ShiftAttendanceMode.FLYING, _("✈ Flying")),
        (ShiftAttendanceMode.FROZEN, _("❄ Frozen")),
    ]
    attendance_mode = models.CharField(
        _("Shift system"),
        max_length=32,
        choices=SHIFT_ATTENDANCE_MODE_CHOICES,
        default=ShiftAttendanceMode.REGULAR,
        blank=False,
    )

    objects = ShiftUserDataQuerySet.as_manager()

    def get_capabilities_display(self):
        return ", ".join(
            [str(SHIFT_USER_CAPABILITY_CHOICES[c]) for c in self.capabilities]
        )

    def get_upcoming_shift_attendances(self):
        return self.user.shift_attendances.filter(
            slot__shift__start_time__gt=timezone.localtime()
        ).with_valid_state()

    def get_account_balance(self, at_date: datetime.datetime | None = None):
        entries = self.user.shift_account_entries
        if at_date:
            entries = entries.filter(date__lte=at_date)
        # Might return None if no objects, so "or 0"
        return entries.aggregate(balance=Sum("value"))["balance"] or 0

    def is_balance_ok(self):
        balance = self.get_account_balance()
        # Depending on when the monthly deduction happens, the balance may fluctuate over the month
        return -1 <= balance

    def is_balance_negative(self):
        return self.get_account_balance() < -1

    def is_balance_positive(self):
        return self.get_account_balance() > 1

    def get_current_shift_exemption(self, date=None):
        if not hasattr(self, "shift_exemptions") or self.shift_exemptions is None:
            return None

        for exemption in self.shift_exemptions.all():
            if exemption.is_active(date):
                return exemption
        return None

    def is_currently_exempted_from_shifts(self, date=None):
        return self.get_current_shift_exemption(date) is not None

    def can_shop(self):
        return self.attendance_mode != ShiftAttendanceMode.FROZEN


def create_shift_user_data(instance: TapirUser, **kwargs):
    if not hasattr(instance, "shift_user_data"):
        ShiftUserData.objects.create(user=instance)


models.signals.post_save.connect(create_shift_user_data, sender=TapirUser)


class ShiftExemption(DurationModelMixin, models.Model):
    shift_user_data = models.ForeignKey(
        ShiftUserData, related_name="shift_exemptions", on_delete=models.CASCADE
    )
    description = models.TextField(_("Description"), null=False, blank=False)

    THRESHOLD_NB_CYCLES_UNREGISTER_FROM_ABCD_SHIFT = 6

    @staticmethod
    def get_attendances_cancelled_by_exemption(
        user: TapirUser, start_date: datetime.date, end_date: datetime.date | None
    ):
        start_time = timezone.make_aware(
            datetime.datetime.combine(start_date, datetime.time(hour=0, minute=0))
        )
        end_time = (
            timezone.make_aware(
                datetime.datetime.combine(end_date, datetime.time(hour=23, minute=59))
            )
            if end_date
            else None
        )

        attendances = ShiftAttendance.objects.filter(
            user=user,
            slot__shift__start_time__gte=start_time,
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
        )

        if end_time:
            attendances = attendances.filter(slot__shift__end_time__lte=end_time)

        if not ShiftExemption.must_unregister_from_abcd_shift(
            start_date=start_date, end_date=end_date
        ):
            return attendances

        for attendance_template in ShiftAttendanceTemplate.objects.filter(user=user):
            attendances = attendances.union(
                ShiftAttendance.objects.filter(
                    slot__in=attendance_template.slot_template.generated_slots.all(),
                    user=user,
                    slot__shift__start_time__gte=start_time,
                )
            )
        return attendances

    @staticmethod
    def must_unregister_from_abcd_shift(
        start_date: datetime.date, end_date: datetime.date | None
    ):
        # Infinite exemption
        if not end_date:
            return True
        return (
            (end_date - start_date).days
            >= ShiftExemption.THRESHOLD_NB_CYCLES_UNREGISTER_FROM_ABCD_SHIFT * 4 * 7
        )


class CreateExemptionLogEntry(LogEntry):
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    template_name = "shifts/log/create_exemption_log_entry.html"

    def populate(
        self,
        start_date: datetime.date,
        end_date: datetime.date | None,
        actor,
        tapir_user,
    ):
        self.start_date = start_date
        self.end_date = end_date
        return super().populate_base(actor=actor, tapir_user=tapir_user)


class UpdateExemptionLogEntry(UpdateModelLogEntry):
    template_name = "shifts/log/update_exemption_log_entry.html"

    def populate(
        self,
        old_frozen: dict,
        new_frozen: dict,
        tapir_user: TapirUser,
        actor: User,
    ):
        return super().populate_base(
            old_frozen=old_frozen,
            new_frozen=new_frozen,
            tapir_user=tapir_user,
            actor=actor,
        )


class ShiftCycleEntry(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shift_user_data", "cycle_start_date"],
                name="user_date_constraint",
            )
        ]

    SHIFT_CYCLE_DURATION = 28

    shift_user_data = models.ForeignKey(
        ShiftUserData, related_name="shift_cycle_logs", on_delete=models.CASCADE
    )
    cycle_start_date = models.DateField(_("Cycle start date"), null=False, blank=False)
    shift_account_entry = models.OneToOneField(
        ShiftAccountEntry,
        related_name="shift_cycle_log",
        on_delete=models.PROTECT,
        null=True,
    )
