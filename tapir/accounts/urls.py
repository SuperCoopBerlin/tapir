from django.urls import path
import django.contrib.auth.views as auth_views
from django.views import generic

from tapir.accounts import views

app_name = "accounts"
urlpatterns = [
    path(
        "", generic.RedirectView.as_view(pattern_name="accounts:user_me"), name="index"
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.logout_then_login,
        name="logout",
    ),
    path("user/me/", views.UserMeView.as_view(), name="user_me"),
    path("user/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("user/<int:pk>/edit", views.UserUpdateView.as_view(), name="user_update"),
]
