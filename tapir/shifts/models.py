from __future__ import annotations

import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from tapir.accounts.models import TapirUser


class ShiftUserCapability:
    SHIFT_COORDINATOR = "shift_coordinator"


SHIFT_USER_CAPABILITY_CHOICES = {
    ShiftUserCapability.SHIFT_COORDINATOR: _("Shift Coordinator"),
}


class ShiftTemplateGroup(models.Model):
    """ShiftTemplateGroup represents a collection of ShiftTemplates that are usually instantiated together.

    Normally, this will be a week of shifts in the ABCD system, so one ShiftTemplateGroup might be "Week A"."""

    name = models.CharField(blank=False, max_length=255)

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    def create_shifts(self, start_date: datetime.date):
        if start_date.weekday() != 0:
            raise ValueError("Start date for shift generation must be a Monday")

        return [
            shift_template.create_shift(start_date=start_date)
            for shift_template in self.shift_templates.all()
        ]


# TODO(Leon Handreke): There must be a library to supply this
WEEKDAY_CHOICES = [
    (0, _("Monday")),
    (1, _("Tuesday")),
    (2, _("Wednesday")),
    (3, _("Thursday")),
    (4, _("Friday")),
    (5, _("Saturday")),
    (6, _("Sunday")),
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
    group = models.ForeignKey(
        ShiftTemplateGroup,
        related_name="shift_templates",
        null=True,
        on_delete=models.PROTECT,
    )

    # NOTE(Leon Handreke): This could be expanded in the future to allow more placement strategies
    # TODO(Leon Handreke): Extra validation to ensure that it is not blank if part of a group
    weekday = models.IntegerField(blank=True, null=True, choices=WEEKDAY_CHOICES)

    start_time = models.TimeField(blank=False)
    end_time = models.TimeField(blank=False)

    def __str__(self):
        display_name = "%s: %s %s %s-%s" % (
            self.__class__.__name__,
            self.name,
            self.get_weekday_display(),
            self.start_time.strftime("%H:%M"),
            self.end_time.strftime("%H:%M"),
        )
        if self.group:
            display_name = "%s (%s)" % (display_name, self.group.name)
        return display_name

    def get_attendance_templates(self):
        return ShiftAttendanceTemplate.objects.filter(
            slot_template__in=self.slot_templates.all()
        )

    def get_display_name(self):
        display_name = "%s %s %s" % (
            self.name,
            self.get_weekday_display(),
            self.start_time.strftime("%H:%M"),
        )
        if self.group:
            display_name = "%s (%s)" % (display_name, self.group.name)
        return display_name

    def _generate_shift(self, start_date: datetime.date):
        shift_date = start_date
        # If this is a shift that is not part of a group and just gets placed manually, just use the day selected
        if self.weekday:
            while True:
                if shift_date.weekday() == self.weekday:
                    break
                shift_date += datetime.timedelta(days=1)

        # TODO(Leon Handreke): Is this timezone user-configurable? Would make sense to use a globally-configurable
        # timezone here, but store aware dates for sure.
        start_time = datetime.datetime.combine(
            shift_date, self.start_time, timezone.localtime().tzinfo
        )
        end_time = datetime.datetime.combine(
            shift_date, self.end_time, timezone.localtime().tzinfo
        )

        return Shift(
            shift_template=self,
            name=self.name,
            start_time=start_time,
            end_time=end_time,
        )

    @transaction.atomic
    def create_shift(self, start_date: datetime.date):
        shift = self._generate_shift(start_date=start_date)

        if Shift.objects.filter(
            shift_template=self, start_time=shift.start_time
        ).exists():
            shift = Shift.objects.get(shift_template=self, start_time=shift.start_time)
        else:
            shift.save()

        for slot_template in self.slot_templates.all():
            ShiftSlot.objects.create(
                slot_template=slot_template,
                name=slot_template.name,
                shift=shift,
                required_capabilities=slot_template.required_capabilities,
                optional=slot_template.optional,
            )

        self.update_future_shift_attendances()

        return shift

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_future_shift_attendances()

    def update_future_shift_attendances(self, now=None):
        for shift in self.generated_shifts.filter(start_time__gt=now or timezone.now()):
            shift.update_attendances_from_template()


class ShiftSlotTemplate(models.Model):
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
    )

    # Whether this ShiftSlot is required to be filled
    optional = models.BooleanField(default=False)

    def get_required_capabilities_display(self):
        return ", ".join([SHIFT_USER_CAPABILITY_CHOICES[c] for c in self.capabilities])

    def get_display_name(self):
        display_name = self.shift_template.get_display_name()
        if self.name:
            display_name += " (%s)" % self.name
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


class ShiftAttendanceTemplate(models.Model):
    user = models.ForeignKey(
        TapirUser, related_name="shift_attendance_templates", on_delete=models.PROTECT
    )
    slot_template = models.OneToOneField(
        ShiftSlotTemplate, related_name="attendance_template", on_delete=models.PROTECT
    )


class Shift(models.Model):
    # ShiftTemplate that this shift was generated from, may be null for manually-created shifts
    shift_template = models.ForeignKey(
        ShiftTemplate,
        null=True,
        blank=True,
        related_name="generated_shifts",
        on_delete=models.PROTECT,
    )

    # TODO(Leon Handreke): For generated shifts, leave this blank instead and use a getter?
    name = models.CharField(blank=False, max_length=255)

    start_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)

    def __str__(self):
        display_name = "%s: %s %s-%s" % (
            self.__class__.__name__,
            self.name,
            self.start_time.strftime("%a %Y-%m-%d %H:%M"),
            self.end_time.strftime("%H:%M"),
        )
        if self.shift_template and self.shift_template.group:
            display_name = "%s (%s)" % (display_name, self.shift_template.group.name)

        display_name = "%s [%d/%d]" % (
            display_name,
            self.get_valid_attendances().count(),
            self.get_required_slots().count(),
        )

        return display_name

    def get_display_name(self):
        display_name = "%s %s" % (
            self.name,
            self.start_time.strftime("%a %Y-%m-%d %H:%M"),
        )
        if self.shift_template and self.shift_template.group:
            display_name = "%s (%s)" % (display_name, self.shift_template.group.name)

        display_name = "%s [%d/%d]" % (
            display_name,
            self.get_valid_attendances().count(),
            self.get_required_slots().count(),
        )

        return display_name

    def get_absolute_url(self):
        return reverse("shifts:shift_detail", args=[self.pk])

    def get_required_slots(self):
        return self.slots.filter(optional=False)

    def get_optional_slots(self):
        return self.slots.filter(optional=True)

    def get_attendances(self) -> ShiftAttendance.ShiftAttendanceQuerySet:
        return ShiftAttendance.objects.filter(slot__in=list(self.slots.all()))

    def get_valid_attendances(self) -> ShiftAttendance.ShiftAttendanceQuerySet:
        return self.get_attendances().with_valid_state()

    def update_attendances_from_template(self):
        """Updates the attendances from the template that this shift was generated from.

        This is used so that when people join or leave a regularly-occurring ShiftTemplate, future shifts already
        generated can be updated to reflect this change."""

        for slot in self.slots.all():
            slot.update_attendances_from_template()


class ShiftSlot(models.Model):
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
    )

    # Whether this ShiftSlot is required to be filled
    optional = models.BooleanField(default=False)

    def get_required_capabilities_display(self):
        return ", ".join([SHIFT_USER_CAPABILITY_CHOICES[c] for c in self.capabilities])

    def update_attendances_from_template(self):
        """Updates the attendances from the template that this slot was generated from.

        This is used so that when people join a regularly-occurring ShiftSlot, future shifts already
        generated can be updated to reflect this change. For users leaving, the update has to be done in the view,
        as we can't know whether the user currently attending the slot just unregistered from the regular slot or
        wants to attend this slot one-time only."""

        if not self.slot_template:
            return

        if not self.get_valid_attendance() and hasattr(
            self.slot_template, "attendance_template"
        ):
            ShiftAttendance.objects.create(
                user=self.slot_template.attendance_template.user, slot=self
            )

    def get_valid_attendance(self):
        return self.attendances.with_valid_state().first()

    def user_can_attend(self, user):
        return (
            # Slot must not be attended yet
            not self.get_valid_attendance()
            and
            # User isn't already registered for this shift
            not self.shift.get_attendances().filter(user=user).exists()
            and
            # User must have all required capabilities
            set(self.required_capabilities).issubset(user.shift_user_data.capabilities)
        )


class ShiftAccountEntry(models.Model):
    """ShiftAccountEntry represents and entry to the shift "bank account" of a user.

    Usually, a user will be debited one credit every four weeks and will be credited one for completing their shift.

    Based on the the account balance and the dates of the entries, the penalties are calculated. For example, if the
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


class ShiftAttendance(models.Model):
    class Meta:
        ordering = ["slot__shift__start_time"]

    class ShiftAttendanceQuerySet(models.QuerySet):
        def with_valid_state(self):
            return self.filter(
                state__in=[ShiftAttendance.State.PENDING, ShiftAttendance.State.DONE]
            )

    objects = ShiftAttendanceQuerySet.as_manager()

    user = models.ForeignKey(
        TapirUser, related_name="shift_attendances", on_delete=models.PROTECT
    )
    slot = models.ForeignKey(
        ShiftSlot, related_name="attendances", on_delete=models.PROTECT
    )

    class State(models.IntegerChoices):
        PENDING = 1
        DONE = 2
        CANCELLED = 3
        MISSED = 4
        MISSED_EXCUSED = 5

    state = models.IntegerField(choices=State.choices, default=State.PENDING)

    # Only filled if state is MISSED_EXCUSED
    excused_reason = models.TextField(blank=True)

    account_entry = models.OneToOneField(
        ShiftAccountEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shift_attendance",
    )

    def mark_done(self):
        self.state = __class__.State.DONE
        # TODO(Leon Handreke): The exact scores here should either be a constant or calculated elsewhere?
        self.account_entry = ShiftAccountEntry.objects.create(
            user=self.user, value=1, date=self.slot.shift.start_time.date()
        )
        self.save()

    def mark_missed(self):
        self.state = __class__.State.MISSED
        # TODO(Leon Handreke): The exact scores here should either be a constant or calculated elsewhere?
        self.account_entry = ShiftAccountEntry.objects.create(
            user=self.user, value=-1, date=self.slot.shift.start_time.date()
        )
        self.save()


class ShiftUserData(models.Model):
    user = models.OneToOneField(
        TapirUser, null=False, on_delete=models.PROTECT, related_name="shift_user_data"
    )

    capabilities = ArrayField(
        models.CharField(
            max_length=128, choices=SHIFT_USER_CAPABILITY_CHOICES.items(), blank=False
        ),
        default=list,
    )

    SHIFT_ATTENDANCE_MODES = [
        ("regular", _("Regular")),
        ("flying", _("Flying")),
    ]

    attendance_mode = models.CharField(
        max_length=32, choices=SHIFT_ATTENDANCE_MODES, default="regular", blank=False
    )

    def get_capabilities_display(self):
        return ", ".join([SHIFT_USER_CAPABILITY_CHOICES[c] for c in self.capabilities])

    def get_upcoming_shift_attendances(self):
        return self.user.shift_attendances.filter(
            slot__shift__start_time__gt=timezone.localtime()
        )

    def get_account_balance(self):
        # Might return None if no objects, so "or 0"
        return (
            self.user.shift_account_entries.aggregate(balance=Sum("value"))["balance"]
            or 0
        )

    def is_balance_ok(self):
        balance = self.get_account_balance()
        # Depending on when the monthly deduction happens, the balance may flucuate over the month
        return -1 <= balance <= 1

    def is_balance_negative(self):
        return self.get_account_balance() < -1

    def is_balance_positive(self):
        return self.get_account_balance() > 1


def create_shift_user_data(instance, **kwargs):
    if not hasattr(instance, "shift_user_data"):
        ShiftUserData.objects.create(user=instance)


models.signals.post_save.connect(create_shift_user_data, sender=TapirUser)
