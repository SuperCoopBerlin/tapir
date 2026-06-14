from django.contrib import admin

from tapir.coop.models import DraftUser, MembershipResignation, ShareOwnership

admin.site.register(ShareOwnership)
admin.site.register(DraftUser)
admin.site.register(MembershipResignation)
