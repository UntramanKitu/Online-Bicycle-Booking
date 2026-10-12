from django.contrib import admin
from .models import Bicycle, Maintenance


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

