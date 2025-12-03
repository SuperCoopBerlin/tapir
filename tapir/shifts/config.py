import datetime

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

GENERATE_UP_TO = datetime.timedelta(days=200)
