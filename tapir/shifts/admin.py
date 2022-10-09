from django.contrib import admin

from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftTemplate,
    Shift,
    ShiftAttendanceTemplate,
    ShiftAttendance,
    ShiftUserData,
    ShiftSlot,
    ShiftSlotTemplate,
)

admin.site.register(ShiftUserData)


class ShiftTemplateInline(admin.TabularInline):
    model = ShiftTemplate
    show_change_link = True
    extra = 3


@admin.register(ShiftTemplateGroup)
class ShiftTemplateGroupAdmin(admin.ModelAdmin):
    inlines = [ShiftTemplateInline]


class ShiftSlotTemplateInline(admin.TabularInline):
    model = ShiftSlotTemplate
    extra = 1


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    inlines = [ShiftSlotTemplateInline, ShiftInline]


class ShiftAttendanceTemplateInline(admin.TabularInline):
    model = ShiftAttendanceTemplate
    extra = 1


@admin.register(ShiftSlotTemplate)
class ShiftSlotTemplateAdmin(admin.ModelAdmin):
    inlines = [ShiftAttendanceTemplateInline]


class ShiftSlotInline(admin.TabularInline):
    model = ShiftSlot
    extra = 1


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    inlines = [ShiftSlotInline]
    list_display = ["name", "start_time", "end_time"]
    search_fields = ["name", "start_time", "end_time"]


class ShiftAttendanceInline(admin.TabularInline):
    model = ShiftAttendance
    extra = 1


@admin.register(ShiftSlot)
class ShiftSlotAdmin(admin.ModelAdmin):
    inlines = [ShiftAttendanceInline]
    list_display = ["name"]
    search_fields = ["name"]
