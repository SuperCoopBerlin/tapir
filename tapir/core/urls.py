from django.urls import path

from tapir.core import views

app_name = "core"
urlpatterns = [
    path(
        "email_list",
        views.EmailListView.as_view(),
        name="email_list",
    ),
]
