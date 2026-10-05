from django.db import models
from django.conf import settings

# โมเดลนี้ใช้เป็นสมุดบันทึกประวัติ (Audit Log) ว่าใครทำอะไรในระบบเมื่อไหร่
class SystemAuditLog(models.Model):
    # ข้อมูลว่าใครเป็นคนทำ (อ้างอิงไปที่บัญชีผู้ใช้)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    
    # บอกว่าทำอะไร (เช่น CREATE, UPDATE, DELETE, LOGIN, LOGOUT)
    action_type = models.CharField(max_length=50)
    
    # ข้อมูลที่ถูกกระทำคืออะไร (เช่น "CampusAnnouncement") และ ID อะไร
    entity_type = models.CharField(max_length=100)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    
    # ข้อมูลเก่าก่อนแก้ และข้อมูลใหม่ที่แก้แล้ว (เก็บเป็นรูปแบบ JSON String)
    old_values = models.TextField(blank=True, default="")
    new_values = models.TextField(blank=True, default="")
    
    # ข้อมูลเครือข่ายและอุปกรณ์
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")
    
    # เวลาที่เกิดเหตุการณ์
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def log_action(cls, user, action_type, entity, old_values=None, new_values=None, request=None):
        import json
        return cls.objects.create(
            user=user,
            action_type=action_type,
            entity_type=entity.__class__.__name__,
            entity_id=getattr(entity, "id", None),
            old_values=json.dumps(old_values) if old_values else "",
            new_values=json.dumps(new_values) if new_values else "",
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        )

    def get_changes_summary(self) -> str:
        return f"{self.action_type} on {self.entity_type} #{self.entity_id}"

    def get_user(self):
        return self.user

    def __str__(self):
        return self.get_changes_summary()
