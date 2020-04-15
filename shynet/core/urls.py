from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path(
        "", RedirectView.as_view(url=reverse_lazy("dashboard:dashboard")), name="index"
    ),
]
