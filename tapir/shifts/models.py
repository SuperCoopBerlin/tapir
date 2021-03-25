import datetime
import enum

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from tapir.accounts.models import TapirUser


class ShiftTemplateGroup(models.Model):
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

    num_slots = models.IntegerField(blank=False, default=3)

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
        start_time = timezone.make_aware(
            datetime.datetime.combine(shift_date, self.start_time)
        )
        end_time = timezone.make_aware(
            datetime.datetime.combine(shift_date, self.end_time)
        )

        return Shift(
            shift_template=self,
            name=self.name,
            start_time=start_time,
            end_time=end_time,
            num_slots=self.num_slots,
        )

    def create_shift(self, start_date: datetime.date):
        shift = self._generate_shift(start_date=start_date)
        shift.save()

        for attendance_template in self.attendance_templates.all():
            ShiftAttendance.objects.create(user=attendance_template.user, shift=shift)

        return shift

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def update_future_shift_attendances(self):
        for shift in self.generated_shifts.filter(
            start_time__gt=datetime.datetime.now()
        ):
            shift.update_attendances_from_shift_template()


class ShiftAttendanceTemplate(models.Model):
    user = models.ForeignKey(
        TapirUser, related_name="shift_attendance_templates", on_delete=models.PROTECT
    )
    shift_template = models.ForeignKey(
        ShiftTemplate, related_name="attendance_templates", on_delete=models.PROTECT
    )


class Shift(models.Model):

    # ShiftTemplate that this shift was generated from, may be null for manually-created shifts
    shift_template = models.ForeignKey(
        ShiftTemplate,
        null=True,
        related_name="generated_shifts",
        on_delete=models.PROTECT,
    )

    # TODO(Leon Handreke): For generated shifts, leave this blank instead and use a getter?
    name = models.CharField(blank=False, max_length=255)

    start_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)

    num_slots = models.IntegerField(blank=False, default=3)

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
            self.num_slots,
        )

        return display_name

    def get_absolute_url(self):
        return reverse("shifts:shift_detail", args=[self.pk])

    def get_valid_attendances(self) -> models.QuerySet:
        return self.attendances.filter(
            state__in=[ShiftAttendance.State.PENDING, ShiftAttendance.State.DONE]
        )

    def update_attendances_from_shift_template(self):
        """Updates the attendances from the template that this shift was generated from.

        This is used so that when people join or leave a regularly-occurring ShiftTemplate, future shifts already
        generated can be updated to reflect this change."""
        if not self.shift_template:
            return

        shift_attendance_template_user_pks = (
            self.shift_template.attendance_templates.values_list("user", flat=True)
        )

        # Remove the attendances that are no longer in the template
        for attendance in self.attendances.all():
            if attendance.user.pk not in shift_attendance_template_user_pks:
                attendance.delete()
        for user_pk in shift_attendance_template_user_pks:
            if user_pk not in self.attendances.values_list("user", flat=True):
                ShiftAttendance.objects.create(shift=self, user=TapirUser(pk=user_pk))


class ShiftAttendance(models.Model):
    user = models.ForeignKey(
        TapirUser, related_name="shift_attendances", on_delete=models.PROTECT
    )
    shift = models.ForeignKey(
        Shift, related_name="attendances", on_delete=models.PROTECT
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


# Represents an entry to the shift "bank account" of the user
class ShiftAccountEntry(models.Model):
    """ShiftAccountEntry represents and entry to the shift "bank account" of a user."""

    user = models.ForeignKey(
        TapirUser, related_name="shift_account_entries", on_delete=models.PROTECT
    )

    # Optional, only if associated with a shift attendance
    shift_attendance = models.OneToOneField(
        ShiftAttendance,
        null=True,
        on_delete=models.SET_NULL,
        related_name="account_entry",
    )

    # Value of the transaction, may be negative (for example for missed shifts)
    value = models.IntegerField(blank=False)
    # Date the transaction is debited, credited
    date = models.DateTimeField(blank=False)
    description = models.CharField(blank=True, max_length=255)


class ShiftUser(object):
    def __init__(self, user):
        self.user = user

    def get_account_entries(self):
        return ShiftAccountEntry.object.filter(user=self.user)
