from django.urls import path

from tapir.log import views

app_name = "log"
urlpatterns = [
    path(
        "<int:pk>/email_content",
        views.email_log_entry_content,
        name="email_log_entry_content",
    ),
    path(
        "text/create/<str:member_type>/<int:member_pk>",
        views.create_text_log_entry,
        name="create_text_log_entry",
    ),
    path(
        "log_overview",
        views.LogTableView.as_view(),
        name="log_overview",
    ),
]
