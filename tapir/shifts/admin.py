from django.contrib import admin

from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    Shift,
    ShiftAttendanceTemplate,
)


class ShiftTemplateInline(admin.TabularInline):
    model = ShiftTemplate
    show_change_link = True
    extra = 3


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(admin.ModelAdmin):
    inlines = [ShiftTemplateInline]


class ShiftAttendanceTemplateInline(admin.TabularInline):
    model = ShiftAttendanceTemplate
    extra = 1

class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    inlines = [ShiftAttendanceTemplateInline, ShiftInline]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass
