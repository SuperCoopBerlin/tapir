import datetime
from calendar import HTMLCalendar, month_name, day_abbr
from functools import cmp_to_key

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import tapir
from tapir.coop.models import ShareOwner
from tapir.shifts.config import DEFAULT_SLOT_ORDER
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftAccountEntry,
    ShiftAttendance,
    SHIFT_ATTENDANCE_MODE_CHOICES,
    ShiftSlotTemplate,
    ShiftSlot,
)
from tapir.utils.shortcuts import get_monday, ensure_date


def generate_shifts_up_to(end_date: datetime.date, start_date=None):
    if start_date is None:
        start_date = timezone.now().date()
    last_monday = get_monday(end_date)
    current_monday = get_monday(start_date)

    while current_monday < last_monday:
        group = get_week_group(current_monday)
        group.create_shifts(current_monday)
        current_monday += datetime.timedelta(days=7)


# override HTMLCalender method to use colors
class ColorHTMLCalendar(HTMLCalendar):
    def __init__(self, firstweekday, monday_to_week_group_map):
        super(ColorHTMLCalendar, self).__init__(firstweekday=firstweekday)
        self.monday_to_week_group_map = monday_to_week_group_map

    def formatweek(self, theweek, monday):
        """
        Return a complete week as a table row.
        """
        s = "".join(self.formatday(d, wd) for (d, wd) in theweek)
        week_group = self.monday_to_week_group_map[monday]
        return f"<tr class='{week_group}' >{s}</tr>"

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a(
            '<table border="0" cellpadding="0" cellspacing="0" class="%s">'
            % self.cssclass_month
        )
        a("\n")
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a("\n")
        a(self.formatweekheader())
        a("\n")
        for week in self.monthdays2calendar(theyear, themonth):
            # for every week, find first day (which of course can be in previous month)
            first_day_of_week_within_month = [day for day in week if day[0] != 0][0]
            d = datetime.date(theyear, themonth, first_day_of_week_within_month[0])
            a(self.formatweek(week, monday=get_monday(d)))
            a("\n")
        a("</table>")
        a("\n")
        return "".join(v)

    def formatyear(self, theyear, width=3):
        """
        Return a formatted year as a table of tables.
        """
        v = []
        a = v.append
        width = max(width, 1)
        a('<table class="legend"><tr>')
        for group in ShiftTemplateGroup.objects.order_by("name"):
            a(f"<td class='{group.name}'>{group.name}</td>")
        a(f"<td class='year'>{theyear}</td>")
        a("</tr></table>")
        a(
            '<table border="0" cellpadding="0" cellspacing="0" class="%s">'
            % self.cssclass_year
        )
        for i in range(1, 1 + 12, width):
            # months in this row
            months = range(i, min(i + width, 13))
            a("<tr>")
            for m in months:
                a("<td style='vertical-align: top;'>")
                a(self.formatmonth(theyear, m, withyear=False))
                a("</td>")
            a("</tr>")
        a("</table>")
        return "".join(v)

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        SuperCoop: Overwrites locale
        """
        return '<th class="%s">%s</th>' % (
            self.cssclasses_weekday_head[day],
            _(day_abbr[day]),
        )

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        SuperCoop: Overwrites locale
        """
        if withyear:
            s = "%s %s" % (month_name[themonth], theyear)
        else:
            s = "%s" % _(month_name[themonth])
        return '<tr><th colspan="7" class="%s">%s</th></tr>' % (
            self.cssclass_month_head,
            s,
        )


def update_shift_account_depending_on_welcome_session_status(share_owner: ShareOwner):
    if share_owner.user is None:
        return
    tapir_user = share_owner.user

    account_entry_from_welcome_session = ShiftAccountEntry.objects.filter(
        user=tapir_user, is_from_welcome_session=True
    )

    if not share_owner.attended_welcome_session:
        account_entry_from_welcome_session.delete()
        return

    if account_entry_from_welcome_session.exists():
        return

    ShiftAccountEntry.objects.create(
        is_from_welcome_session=True,
        user=tapir_user,
        description="Welcome session / Willkommenstreffen",
        date=datetime.date.today(),
        value=1,
    )


def get_ids_of_users_registered_to_a_shift_with_capability(capability_id):
    return (
        ShiftAttendance.objects.filter(
            slot__required_capabilities__id=capability_id,
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
        )
        .distinct()
        .values_list("user__id", flat=True)
    )


def get_attendance_mode_display(attendance_mode: str) -> str:
    for mode_choice in SHIFT_ATTENDANCE_MODE_CHOICES:
        if mode_choice[0] == attendance_mode:
            return mode_choice[1]
    return _(f"Unknown mode {attendance_mode}")


def sort_slots_by_name(slots: list[ShiftSlot] | list[ShiftSlotTemplate]):
    def compare_slots_by_name(slot_a, slot_b):
        name_a = slot_a.name.casefold()
        name_b = slot_b.name.casefold()

        if name_a in DEFAULT_SLOT_ORDER and name_b not in DEFAULT_SLOT_ORDER:
            return -1
        if name_a not in DEFAULT_SLOT_ORDER and name_b in DEFAULT_SLOT_ORDER:
            return 1
        if name_a in DEFAULT_SLOT_ORDER and name_b in DEFAULT_SLOT_ORDER:
            return DEFAULT_SLOT_ORDER.index(name_a) - DEFAULT_SLOT_ORDER.index(name_b)
        if name_a < name_b:
            return -1
        if name_b < name_a:
            return 1
        return 0

    return sorted(slots, key=cmp_to_key(compare_slots_by_name))


def get_week_group(
    target_date, cycle_start_dates=None, shift_groups_count: int | None = None
) -> ShiftTemplateGroup | None:
    if shift_groups_count is None:
        shift_groups_count = ShiftTemplateGroup.objects.count()

    if shift_groups_count == 0:
        # Many tests run without creating any ShiftTemplateGroup but still call get_week_group
        return None

    target_date = ensure_date(target_date)
    target_date = get_monday(target_date)

    if cycle_start_dates is None:
        cycle_start_dates = tapir.shifts.config.cycle_start_dates

    if cycle_start_dates[0] > target_date:
        ref_date = cycle_start_dates[0]
    else:
        # Get the highest date that is before target_date
        ref_date = [
            get_monday(cycle_start_date)
            for cycle_start_date in cycle_start_dates
            if cycle_start_date <= target_date
        ][-1]
    delta_weeks = ((target_date - ref_date).days / 7) % shift_groups_count
    return ShiftTemplateGroup.get_group_from_index(delta_weeks)
