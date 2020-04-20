from django.contrib import admin

from .models import Hit, Session


class HitInline(admin.TabularInline):
    model = Hit
    fk_name = "session"
    extra = 0


class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "service",
        "start_time",
        "last_seen",
        "identifier",
        "ip",
        "asn",
        "country",
    )
    list_display_links = ("uuid",)
    search_fields = (
        "ip",
        "user_agent",
        "device",
        "device_type",
        "identifier",
        "asn",
        "time_zone",
    )
    list_filter = ("device_type",)
    inlines = [HitInline]


admin.site.register(Session, SessionAdmin)


class HitAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "initial",
        "start_time",
        "heartbeats",
        "tracker",
        "load_time",
        "location",
    )
    list_display_links = ("session",)
    search_fields = ("initial", "tracker", "location", "referrer")
    list_filter = ("initial", "tracker")


admin.site.register(Hit, HitAdmin)
