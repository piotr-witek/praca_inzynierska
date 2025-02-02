from django.contrib import admin
from django.urls import include, path

import accounts.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", accounts.views.loginaccount, name="index"),
    path("accounts/", include("accounts.urls")),
    path("inventory/", include("inventory.urls")),
    path("dashboard/", include("dashboard.urls")),
]
