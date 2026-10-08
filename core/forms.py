from django import forms
from .models import UnifiedUser, Bicycle, Maintenance


class UnifiedUserForm(forms.ModelForm):
    class Meta:
        model = UnifiedUser
        fields = [
            "username", "password_hash", "email", "first_name", "last_name",
            "student_id", "faculty", "department", "phone", "role", "status"
        ]
        labels = {"password_hash": "Password"}
        widgets = {
            "password_hash": forms.PasswordInput(render_value=True),
        }


class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = [
            "bike_code", "brand", "model", "color", "frame_number",
            "status", "current_location", "qr_code", "purchase_date",
            "purchase_price", "total_rides"
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
        }


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = [
            "bicycle", "reported_by", "assigned_to", "type", "description",
            "status", "parts_replaced", "cost", "start_date", "end_date"
        ]
        labels = {"assigned_to": "Assigned to (staff officer ID)"}
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "parts_replaced": forms.Textarea(attrs={"rows": 3}),
        }
