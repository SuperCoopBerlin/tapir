import datetime

from tapir.utils.shortcuts import get_timezone_aware_datetime

cycle_start_dates = [
    datetime.date(year=2022, month=4, day=11),
]
cycle_start_dates.sort()

REMINDER_EMAIL_DAYS_BEFORE_SHIFT = 9
FLYING_MEMBERS_REGISTRATION_REMINDER_DAYS_AFTER_CYCLE_START = 7

FREEZE_THRESHOLD = -4
FREEZE_AFTER_DAYS = 10
NB_WEEKS_IN_THE_FUTURE_FOR_MAKE_UP_SHIFTS = 8

FEATURE_FLAG_SHIFT_PARTNER = "feature_flags.shifts.shift_partner"
FEATURE_FLAG_FLYING_MEMBERS_REGISTRATION_REMINDER = (
    "feature_flags.shifts.flying_members_registration_reminder"
)

ATTENDANCE_MODE_REFACTOR_DATE = datetime.date(year=2024, month=11, day=11)
ATTENDANCE_MODE_REFACTOR_DATETIME = get_timezone_aware_datetime(
    ATTENDANCE_MODE_REFACTOR_DATE, datetime.time(hour=0, minute=0)
)
