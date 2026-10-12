from django.conf import settings
from django.db import models


class Bicycle(models.Model):
    """Table 2: Bicycle Management (ported from fluke)."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        IN_USE = "in_use", "In Use"
        UNDER_MAINTENANCE = "under_maintenance", "Under Maintenance"
        RETIRED = "retired", "Retired"

    bike_code = models.CharField(max_length=50, unique=True)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    frame_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AVAILABLE)
    current_location = models.CharField(max_length=255)
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_rides = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bicycle"
        ordering = ["id"]

    def __str__(self):
        return self.bike_code


class Maintenance(models.Model):
    """Table 3: Maintenance (ported from fluke, reporter -> accounts.UnifiedUser)."""

    class MaintenanceType(models.TextChoices):
        REPAIR = "repair", "Repair"
        ROUTINE_CHECK = "routine_check", "Routine Check"
        PART_REPLACEMENT = "part_replacement", "Part Replacement"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    bicycle = models.ForeignKey(
        Bicycle,
        on_delete=models.CASCADE,
        related_name="maintenances",
        db_column="bicycle_id",
    )
    # NOTE: fluke pointed this at its own core.UnifiedUser; here it points
    # at the monolith's real user model (accounts.UnifiedUser).
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_maintenances",
        db_column="reported_by",
    )
    # Schema v2 refers to staff_officer.id; kept as integer like fluke.
    assigned_to = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=30, choices=MaintenanceType.choices)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    parts_replaced = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "maintenance"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Maintenance #{self.id} - {self.bicycle.bike_code}"

