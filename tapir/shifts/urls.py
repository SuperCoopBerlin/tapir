from django.urls import path, include
from django.views import generic

from tapir.shifts import views

app_name = "shifts"
urlpatterns = [
    path(
        "/",
        generic.RedirectView.as_view(pattern_name="shifts:shift_upcoming"),
        name="index",
    ),
    path("upcoming/", views.UpcomingDaysView.as_view(), name="shift_upcoming"),
    # TODO(Leon Handreke): Can we somehow introduce a sub-namespace here?
    path("shift/<int:pk>/", views.ShiftDetailView.as_view(), name="shift_detail"),
    path(
        "shift/<int:pk>/done",
        views.mark_shift_attendance_done,
        name="mark_shiftattendance_done",
    ),
    path(
        "shift/<int:pk>/missed",
        views.mark_shift_attendance_missed,
        name="mark_shiftattendance_missed",
    ),
    path("populate_shifts", views.populate_shifts, name="populate_shifts",),
    path(
        "populate_user_shifts/<int:user_id>",
        views.populate_user_shifts,
        name="populate_user_shifts",
    ),
]
