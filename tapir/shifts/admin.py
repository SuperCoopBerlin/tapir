from django.contrib import admin

from tapir.shifts.models import ShiftTemplateGroup, ShiftTemplate, Shift



class ShiftTemplateInline(admin.TabularInline):
    model = ShiftTemplate


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(admin.ModelAdmin):
    inlines = [
        ShiftTemplateInline
    ]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass
