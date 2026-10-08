from django.contrib import admin
from .models import UnifiedUser, Bicycle, Maintenance


@admin.register(UnifiedUser)
class UnifiedUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "student_id", "role", "status")
    list_filter = ("role", "status")
    search_fields = ("username", "email", "student_id", "first_name", "last_name")


@admin.register(Bicycle)
class BicycleAdmin(admin.ModelAdmin):
    list_display = ("id", "bike_code", "brand", "model", "status", "current_location", "total_rides")
    list_filter = ("status", "brand")
    search_fields = ("bike_code", "brand", "model", "frame_number")


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ("id", "bicycle", "reported_by", "type", "status", "cost", "start_date", "end_date")
    list_filter = ("type", "status")
    search_fields = ("bicycle__bike_code", "description")
