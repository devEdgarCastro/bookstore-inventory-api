"""Root URL configuration.

The public API is mounted at the site root (no /api prefix) because the
technical test requires POST /books.
"""

from django.contrib import admin
from django.urls import include, path

from books.views import HealthzView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", HealthzView.as_view(), name="healthz"),
    path("", include("books.urls")),
]
