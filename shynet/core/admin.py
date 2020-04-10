from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Service, User

admin.site.register(User, UserAdmin)
admin.site.register(Service)
