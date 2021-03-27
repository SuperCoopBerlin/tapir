from django.contrib import admin
from django.contrib.auth.models import Group

from tapir.accounts.models import TapirUser

admin.site.register(TapirUser)
