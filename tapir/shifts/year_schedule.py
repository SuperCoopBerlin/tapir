import calendar
import datetime


# override HTMLCalender method to use colors
# TODO locale einpflegen
class ColorHTMLCalendar(calendar.HTMLCalendar):
    def __init__(self, firstweekday, shift_color_dict):
        super(ColorHTMLCalendar, self).__init__(firstweekday=firstweekday)
        self.shift_colors = {
            "A": "#A19C6E",
            "B": "#2A747F",
            "C": "#CF7730",
            "D": "#992927",
        }
        self.shift_color_dict = self.colorkey(shift_color_dict)

    def colorkey(self, shiftdatedict):
        """
        Replace shift name with color from class variable
        """
        for key, value in shiftdatedict.items():
            shiftdatedict[key] = self.shift_colors[value]
        return shiftdatedict

    def formatweek(self, theweek, shift_key):
        """
        Return a complete week as a table row.
        """
        s = "".join(self.formatday(d, wd) for (d, wd) in theweek)
        return '<tr style="background-color:%s">%s</tr>' % (
            self.shift_color_dict[shift_key],
            s,
        )

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
            # TODO is there a nicer way to find first non-zero in list of tuples?
            firstdayofweekwithinmonth = list(filter(lambda x: x[0] != 0, week))[0][0]
            d = datetime.date(theyear, themonth, firstdayofweekwithinmonth)
            firstdayofweek = d - datetime.timedelta(days=d.weekday() % 7)
            a(self.formatweek(week, shift_key=firstdayofweek))
            a("\n")
        a("</table>")
        a("\n")
        return "".join(v)
