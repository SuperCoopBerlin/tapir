from decimal import Decimal

COOP_SHARE_PRICE = Decimal(100)
COOP_ENTRY_AMOUNT = Decimal(10)
COOP_MIN_SHARES = 1
COOP_DEFAULT_SHARES = 5
COOP_MAX_SHARES = 5000

on_welcome_session_attendance_update = []
# This is not very clean, we need a better solution to inject member filters from the shift app into the coop app
# without adding a dependency from the coop app to the shift app
get_ids_of_users_registered_to_a_shift_with_capability = []
