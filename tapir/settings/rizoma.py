# Custom settings for Rizoma overwrites

from .shared import *
from .env import (env, BASE_DIR)

LANGUAGE_CODE = "pt" # PT?!?
PHONENUMBER_DEFAULT_REGION = "PT"
TIME_ZONE = "Europe/Lisbon"

# FIXME: we probably need to update these for rizoma

EMAIL_ADDRESS_MEMBER_OFFICE = "mitglied@rizomacoop.pt "
EMAIL_ADDRESS_ACCOUNTING_TEAM = "accounting@rizomacoop.pt "
EMAIL_ADDRESS_ACCOUNTING_SOFTWARE = env.str(
    "EMAIL_ADDRESS_ACCOUNTING_SOFTWARE", default=None
)
EMAIL_ADDRESS_MANAGEMENT = "contact@rizomacoop.pt "
EMAIL_ADDRESS_SUPERVISORS = "aufsichtsrat@rizomacoop.pt "

COOP_NAME = "Rizoma"
COOP_FULL_NAME = "Rizoma Cooperativa Integral "
COOP_STREET = "R. José Estêvão 4"
COOP_PLACE = "1150-192 Lisboa, Portugal"
FROM_EMAIL_MEMBER_OFFICE = f"{COOP_NAME} Membros <{EMAIL_ADDRESS_MEMBER_OFFICE}>"
DEFAULT_FROM_EMAIL = FROM_EMAIL_MEMBER_OFFICE


# we need to add our rizoma app
INSTALLED_APPS.append("tapir.rizoma")

ACTIVE_LOGIN_BACKEND = env.str("ACTIVE_LOGIN_BACKEND", default="coops.pt")
if ACTIVE_LOGIN_BACKEND == LOGIN_BACKEND_COOPS_PT:
    AUTHENTICATION_BACKENDS = ["tapir.rizoma.coops_pt_auth_backend.CoopsPtAuthBackend"]
    COOPS_PT_API_BASE_URL = env.str("COOPS_PT_API_BASE_URL", default="https://api.demo.coops.pt")
    COOPS_PT_API_KEY = env.str("COOPS_PT_API_KEY", default="invalid_key")
    COOPS_PT_RSA_PUBLIC_KEY_FILE_PATH = env.str("COOPS_PT_RSA_PUBLIC_KEY_FILE_PATH", default="")

# we prefix all templates with our custom rizoma templates
TEMPLATES[0]['DIRS'].insert(0, os.path.join(BASE_DIR, "rizoma/templates"))

# we have to upadte the celery background jobs to sync our users
CELERY_BEAT_SCHEDULE.update(
    {
        "sync_users_with_coops_pt_backend": {
            "task": "tapir.rizoma.tasks.sync_users_with_coops_pt_backend",
            "schedule": celery.schedules.crontab(hour="*", minute="0"),
        },
    }
)

LOGIN_REDIRECT_URL = "/shifts/dashboard"