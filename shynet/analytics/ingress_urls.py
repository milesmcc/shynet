from django.contrib import admin
from django.urls import include, path

from .views import ingress

urlpatterns = [
    path(
        "<service_uuid>/pixel.gif", ingress.PixelView.as_view(), name="endpoint_pixel"
    ),
    path(
        "<service_uuid>/script.js", ingress.ScriptView.as_view(), name="endpoint_script"
    ),
    path(
        "<service_uuid>/<identifier>/pixel.gif",
        ingress.PixelView.as_view(),
        name="endpoint_pixel_id",
    ),
    path(
        "<service_uuid>/<identifier>/script.js",
        ingress.ScriptView.as_view(),
        name="endpoint_script_id",
    ),
]
