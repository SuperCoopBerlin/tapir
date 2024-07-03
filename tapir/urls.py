"""tapir URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views import generic

from tapir.settings import ENABLE_SILK_PROFILING

urlpatterns = [
    path("", generic.RedirectView.as_view(pattern_name="accounts:index")),
    path("admin/", admin.site.urls),
    path("accounts/", include("tapir.accounts.urls")),
    path("shifts/", include("tapir.shifts.urls")),
    path("coop/", include("tapir.coop.urls")),
    path("log/", include("tapir.log.urls")),
    path("core/", include("tapir.core.urls")),
    path("statistics/", include("tapir.statistics.urls")),
    path("welcomedesk/", include("tapir.welcomedesk.urls")),
    path("financingcampaign/", include("tapir.financingcampaign.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if ENABLE_SILK_PROFILING:
    urlpatterns += [url(r"^silk/", include("silk.urls", namespace="silk"))]
