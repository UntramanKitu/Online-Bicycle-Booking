from django.contrib import admin
from .models import SystemAuditLog

# =========================================================================
# ระบบหลังบ้านสำหรับประวัติการทำงาน (Audit Admin)
# =========================================================================

# ทะเบียนประวัติ (Audit Log) เป็นข้อมูลที่สำคัญมาก ห้ามแก้ไขเด็ดขาด เราจึงต้องล็อกไว้หมด
@admin.register(SystemAuditLog)
class SystemAuditLogAdmin(admin.ModelAdmin):
    # คอลัมน์ที่โชว์หน้ารวม: ดูว่าใครทำอะไร กับข้อมูลไหน ตอนไหน 
    list_display = ('user', 'action_type', 'entity_type', 'entity_id', 'ip_address', 'created_at')
    
    # กรองดูง่ายๆ ว่าอยากดูประวัติการสร้าง (CREATE) การลบ (DELETE) หรือเข้าสู่ระบบ (LOGIN)
    list_filter = ('action_type', 'entity_type', 'created_at')
    
    # ค้นหาจากไอพี หรือชื่อผู้กระทำได้เลย
    search_fields = ('user__username', 'ip_address', 'action_type')
    
    # สำคัญที่สุด! ฟังก์ชันนี้ทำให้ "ไม่สามารถเพิ่ม ลด หรือแก้ไขประวัติ" ได้ผ่านหน้าหลังบ้าน 
    # (ประวัติต้องเป็นของจริงที่ระบบสร้างอัตโนมัติเท่านั้น)
    
    def has_add_permission(self, request):
        return False # ห้ามเพิ่มข้อมูลประวัติเอง

    def has_change_permission(self, request, obj=None):
        return False # ห้ามแก้ไขข้อมูลประวัติ

    def has_delete_permission(self, request, obj=None):
        return False # ห้ามลบข้อมูลประวัติ (ถ้าอยากลบ ต้องไปลบในฐานข้อมูลโดยตรง)
