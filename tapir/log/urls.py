from django.urls import path

from tapir.log import views

app_name = "log"
urlpatterns = [
    path(
        "<int:pk>/email_content",
        views.email_log_entry_content,
        name="email_log_entry_content",
    )
]
