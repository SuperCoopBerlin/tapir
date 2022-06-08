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
        "text/create/user/<int:user_pk>",
        views.create_text_log_entry,
        name="create_user_text_log_entry",
    ),
    path(
        "text/create/shareowner/<int:shareowner_pk>",
        views.create_text_log_entry,
        name="create_share_owner_text_log_entry",
    ),
    path(
        "log_overview",
        views.LogTableView.as_view(),
        name="log_overview",
    ),
]
