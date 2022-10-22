from django.urls import path, include
from rest_framework import routers

# Serializers define the API representation.
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from tapir.api.views import (
    ShareOwnerView,
    TapirUserView,
    UserCapabilitiesView,
    ShiftsNeedingHelpView,
    UpcomingShiftView,
)

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("user/", TapirUserView.as_view(), name="get_tapir_user"),
    path("share_owner/", ShareOwnerView.as_view(), name="get_share_owner"),
    path(
        "shift/upcoming/",
        UpcomingShiftView.as_view(),
        name="get_upcoming_shift_attendance",
    ),
    path(
        "shift/needs_help/",
        ShiftsNeedingHelpView.as_view(),
        name="list_shifts_needing_help",
    ),
    path(
        "user/capabilities/", UserCapabilitiesView.as_view(), name="user_capabilities"
    ),
]
