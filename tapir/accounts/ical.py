from django_ical.views import ICalFeed


class ShiftCalendarICalFeed(ICalFeed):
    product_id = '-//supercoop.de//ShiftCalendar//EN'
    timezone = 'UTC'
    file_name = "supercoop.ics"

    def items(self):
        print(dir(self))
        return []

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_start_datetime(self, item):
        return item.start_datetime
