"""shynet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
import debug_toolbar

urlpatterns = [
    path("__debug__/", include(debug_toolbar.urls)),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("ingress/", include(("analytics.ingress_urls", "ingress")), name="ingress"),
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
    path("healthz/", include("health_check.urls")),
    path("", include(("core.urls", "core"), namespace="core")),
    path("api/v1/", include(("api.urls", "api"), namespace="api")),
]
