from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    AuditLog,
    Clinic,
    ClosedWindow,
    Doctor,
    Encounter,
    OccasionalSchedule,
    Patient,
    RecurringSchedule,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "is_staff"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    search_fields = ["email"]


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ["name", "cnpj", "phone", "email", "city", "state"]
    search_fields = ["name", "cnpj", "city"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["user", "specialty", "license_number"]
    search_fields = ["user__email", "specialty", "license_number"]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "date_of_birth", "sex", "phone"]
    search_fields = ["first_name", "last_name", "email"]
    list_filter = ["sex"]


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "status", "scheduled_at"]
    list_filter = ["status", "scheduled_at"]
    search_fields = ["patient__first_name", "patient__last_name"]


@admin.register(RecurringSchedule)
class RecurringScheduleAdmin(admin.ModelAdmin):
    list_display = ["doctor", "weekday", "start_time", "end_time", "interval_weeks", "slot_duration"]
    list_filter = ["weekday", "doctor"]
    ordering = ["doctor", "weekday", "start_time"]


@admin.register(ClosedWindow)
class ClosedWindowAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "is_full_day", "start_time", "end_time", "reason"]
    list_filter = ["is_full_day", "doctor", "date"]
    ordering = ["doctor", "date"]


@admin.register(OccasionalSchedule)
class OccasionalScheduleAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "start_time", "end_time", "slot_duration"]
    list_filter = ["doctor", "date"]
    ordering = ["doctor", "date", "start_time"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "action", "model_name", "object_id", "description"]
    list_filter = ["action", "model_name"]
    search_fields = ["description", "user__email"]
    readonly_fields = ["user", "action", "model_name", "object_id", "description", "timestamp"]
