import django.contrib.auth.views as auth_views
from django.urls import path, include, reverse_lazy
from django.views import generic

from tapir.accounts import views

accounts_urlpatterns = [
    path(
        "", generic.RedirectView.as_view(pattern_name="accounts:user_me"), name="index"
    ),
    path("user/me/", views.TapirUserMeView.as_view(), name="user_me"),
    path("user/<int:pk>/", views.TapirUserDetailView.as_view(), name="user_detail"),
    path("user/<int:pk>/edit", views.TapirUserUpdateView.as_view(), name="user_update"),
    path(
        "user/<int:pk>/send_welcome_email",
        views.send_user_welcome_email,
        name="send_user_welcome_email",
    ),
    path(
        "user/<int:pk>/update_purchase_tracking_allowed/<int:allowed>",
        views.UpdatePurchaseTrackingAllowedView.as_view(),
        name="update_purchase_tracking_allowed",
    ),
    path(
        "user/<int:pk>/member_card_barcode_pdf",
        views.member_card_barcode_pdf,
        name="member_card_barcode_pdf",
    ),
    path(
        "user/<int:pk>/edit_ldap_groups",
        views.EditUserLdapGroupsView.as_view(),
        name="edit_user_ldap_groups",
    ),
]

urlpatterns = [
    # Standard login/logout/password views should be un-namespaced because Django refers to them in a few places and
    # it's easier to do it like this than hunt down all the places and fix the references
    path("", include((accounts_urlpatterns, "accounts"))),
    path(
        "login/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.logout_then_login,
        name="logout",
    ),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            success_url=reverse_lazy("accounts:user_me"),
            template_name="registration/password_update.html",
        ),
        name="password_change",
    ),
    path(
        "password_reset/",
        views.PasswordResetView.as_view(
            html_email_template_name="registration/email/password_reset_email.html",
            subject_template_name="registration/email/password_reset_subject.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
