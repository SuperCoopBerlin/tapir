from calendar import HTMLCalendar, month_name, day_abbr
from datetime import datetime, timedelta, date

from django.utils.translation import gettext_lazy as _

from tapir.shifts.models import ShiftTemplateGroup
from tapir.shifts.templatetags.shifts import get_week_group
from tapir.utils.shortcuts import get_monday


def generate_shifts_up_to(target_day: datetime.date):
    target_monday = target_day - timedelta(days=target_day.weekday())
    current_monday = date.today() - timedelta(days=date.today().weekday())

    while current_monday < target_monday:
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
