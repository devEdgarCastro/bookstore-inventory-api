"""Root URL configuration.

The books API is wired in the following commit; this keeps the project
bootable (`manage.py check`) at every point in history.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
