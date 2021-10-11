from django.contrib import admin
from api.models import ApiToken


class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "value")


admin.site.register(ApiToken, ApiTokenAdmin)
