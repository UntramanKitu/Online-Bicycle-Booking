from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import SystemAuditLog

# ฟังก์ชันดักจับ (Signal) เมื่อมีคน "เข้าสู่ระบบ (Login)" สำเร็จ
@receiver(user_logged_in)
def log_login(sender, user, request, **kwargs):
    SystemAuditLog.objects.create(user=user, action_type="LOGIN", entity_type="User", entity_id=user.id, ip_address=request.META.get('REMOTE_ADDR'))

# ฟังก์ชันดักจับ (Signal) เมื่อมีคน "ออกจากระบบ (Logout)"
@receiver(user_logged_out)
def log_logout(sender, user, request, **kwargs):
    SystemAuditLog.objects.create(user=user, action_type="LOGOUT", entity_type="User", entity_id=user.id, ip_address=request.META.get('REMOTE_ADDR'))