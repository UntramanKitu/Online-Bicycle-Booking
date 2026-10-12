from django.conf import settings
from django.db import DatabaseError

from .models import Maintenance


def nav_counts(request):
    """Number of maintenance reports waiting for triage, shown as a badge in the sidebar."""
    try:
        pending = Maintenance.objects.filter(status=Maintenance.Status.PENDING).count()
    except DatabaseError:
        pending = 0
    return {"nav_pending": pending}


def social_providers(request):
    """
    เปิด/ปิดปุ่มล็อกอินผ่าน Google ในหน้า login
    โชว์ปุ่มก็ต่อเมื่อตั้งค่า GOOGLE_OAUTH2_KEY/SECRET ใน .env เรียบร้อยเท่านั้น
    """
    google_enabled = bool(
        getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
        and getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")
    )
    return {"social_google_enabled": google_enabled}
