import datetime

from tapir.core.tapir_email_base import all_emails
from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmail

cycle_start_dates = [
    datetime.date(year=2022, month=4, day=11),
]
cycle_start_dates.sort()

REMINDER_EMAIL_DAYS_BEFORE_SHIFT = 7

# Usually emails are registered to all_emails in the same file as the email's class, but since
# ShiftReminderEmail is only called by celery, we need to import it somewhere else
all_emails[ShiftReminderEmail.get_unique_id()] = ShiftReminderEmail
