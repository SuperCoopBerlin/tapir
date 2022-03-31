from datetime import datetime, timedelta, date

from tapir.shifts.templatetags.shifts import get_week_group
from tapir.utils.shortcuts import get_monday


def generate_shifts_up_to(end_date: datetime.date, start_date=date.today()):
    last_monday = get_monday(end_date)
    current_monday = get_monday(start_date)

    while current_monday < last_monday:
        current_monday += timedelta(days=7)
        group = get_week_group(current_monday)
        group.create_shifts(current_monday)
