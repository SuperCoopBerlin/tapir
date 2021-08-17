from django.urls import path
from django.views import generic

from tapir.shifts import views

app_name = "shifts"
urlpatterns = [
    path(
        "",
        generic.RedirectView.as_view(pattern_name="shifts:shift_upcoming"),
        name="index",
    ),
    path(
        "user/<int:user_pk>/set_user_attendance_mode_flying",
        views.set_user_attendance_mode_flying,
        name="set_user_attendance_mode_flying",
    ),
    path(
        "user/<int:user_pk>/set_user_attendance_mode_regular",
        views.set_user_attendance_mode_regular,
        name="set_user_attendance_mode_regular",
    ),
    path("upcoming/", views.UpcomingDaysView.as_view(), name="shift_upcoming"),
    # TODO(Leon Handreke): Can we somehow introduce a sub-namespace here?
    path("shift/<int:pk>/", views.ShiftDetailView.as_view(), name="shift_detail"),
    path(
        "shift/create",
        views.CreateShiftView.as_view(),
        name="shift_create",
    ),
    path(
        "shiftslot/<int:pk>/register/<int:user_pk>",
        views.shiftslot_register_user,
        name="shiftslot_register_user",
    ),
    path(
        "shift/<int:pk>/edit",
        views.EditShiftView.as_view(),
        name="shift_edit",
    ),
    path(
        "shiftattendance/<int:pk>/done",
        views.mark_shift_attendance_done,
        name="mark_shiftattendance_done",
    ),
    path(
        "shiftattendance/<int:pk>/missed",
        views.mark_shift_attendance_missed,
        name="mark_shiftattendance_missed",
    ),
    path(
        "shifttemplate/<int:pk>",
        views.ShiftTemplateDetail.as_view(),
        name="shift_template_detail",
    ),
    path(
        "shifttemplate/overview",
        views.ShiftTemplateOverview.as_view(),
        name="shift_template_overview",
    ),
    path(
        "shifttemplate/overview/register/<int:user_pk>",
        views.ShiftTemplateOverviewRegister.as_view(),
        name="shift_template_overview_register",
    ),
    path(
        "shifttemplate/<int:pk>/register/<int:user_pk>",
        views.shifttemplate_register_user,
        name="shifttemplate_register_user",
    ),
    path(
        "slottemplate/<int:slot_template_pk>/register",
        views.SlotTemplateRegisterView.as_view(),
        name="slottemplate_register",
    ),
    path(
        "shift_attendance_template/<int:pk>/delete",
        views.shift_attendance_template_delete,
        name="shift_attendance_template_delete",
    ),
    path(
        "timetable",
        views.UpcomingShiftsAsTimetable.as_view(),
        name="upcoming_timetable",
    ),
]
