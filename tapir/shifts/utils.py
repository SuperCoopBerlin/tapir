from calendar import HTMLCalendar, month_name, day_abbr
from datetime import datetime, timedelta, date

from django.utils.translation import gettext_lazy as _

from tapir.coop.models import ShareOwner
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftAccountEntry,
    ShiftAttendance,
    ShiftUserCapability,
)
from tapir.shifts.templatetags.shifts import get_week_group
from tapir.utils.shortcuts import get_monday


def generate_shifts_up_to(end_date: datetime.date, start_date=date.today()):
    last_monday = get_monday(end_date)
    current_monday = get_monday(start_date)

    while current_monday < last_monday:
        current_monday += timedelta(days=7)
        group = get_week_group(current_monday)
        group.create_shifts(current_monday)


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
            d = date(theyear, themonth, first_day_of_week_within_month[0])
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
        date=datetime.today(),
        value=1,
    )


def get_ids_of_users_registered_to_a_shift_with_capability(
    capability: ShiftUserCapability,
):
    return (
        ShiftAttendance.objects.filter(
            slot__required_capabilities__contains=[capability],
            state__in=ShiftAttendance.STATES_WHERE_THE_MEMBER_IS_EXPECTED_TO_SHOW_UP,
        )
        .distinct()
        .values_list("user__id", flat=True)
    )
