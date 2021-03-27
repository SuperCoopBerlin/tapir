from django.contrib import admin
from django.contrib.auth.models import Group

from tapir.accounts.models import TapirUser, DraftUser

admin.site.register(TapirUser)
admin.site.register(DraftUser)
