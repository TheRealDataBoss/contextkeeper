"""Root URL configuration for contextkeeper SaaS."""

from django.contrib import admin
from django.urls import include, path

from apps.dashboard.views import index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include("apps.api.urls")),
    path("billing/", include("apps.billing.urls")),
    path("settings/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", index, name="index"),
]
