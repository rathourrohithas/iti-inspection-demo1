from django.contrib import admin

from .models import ITI, Attachment, AuditLog, Inspection, PortalSettings, Profile, TeamMember


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "designation", "office")
    list_filter = ("role",)


@admin.register(ITI)
class ITIAdmin(admin.ModelAdmin):
    list_display = ("name", "mis_code", "district", "ownership", "active")
    search_fields = ("name", "mis_code", "district")


class TeamInline(admin.TabularInline):
    model = TeamMember
    extra = 0


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("iti", "team_name", "scheduled_date", "deadline", "status", "progress_pct")
    list_filter = ("status",)
    inlines = [TeamInline]
    readonly_fields = ("data", "version")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "inspection", "field_key")
    list_filter = ("action",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Attachment)
admin.site.register(PortalSettings)
