from datetime import datetime, timedelta, date

from tapir.shifts.templatetags.shifts import get_week_group


def generate_shifts_up_to(target_day: datetime.date):
    target_monday = target_day - timedelta(days=target_day.weekday())
    current_monday = date.today() - timedelta(days=date.today().weekday())

    while current_monday < target_monday:
        current_monday += timedelta(days=7)
        group = get_week_group(current_monday)
        group.create_shifts(current_monday)
