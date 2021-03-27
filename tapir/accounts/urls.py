from django.urls import path
import django.contrib.auth.views as auth_views
from django.views import generic

from tapir.shifts import views

app_name = "accounts"
urlpatterns = [
    path("/", generic.RedirectView.as_view(pattern_name="user_profile"), name="index"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout",),
    path("user/me/", views.UserMeView.as_view(), name="user_me"),
    path("user/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
]
