from django.urls import path, include

from tapir.shifts import views

app_name = "shifts"
urlpatterns = [
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
]
