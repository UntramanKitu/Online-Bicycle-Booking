from django.contrib import admin
from .models import StaffProfile

# =========================================================================
# ระบบหลังบ้านสำหรับประวัติเจ้าหน้าที่ (Staff Admin)
# =========================================================================

# นำตาราง StaffProfile ไปแสดงในหน้าหลังบ้านของ Django
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    # กำหนดคอลัมน์ที่จะโชว์ในหน้ารายชื่อเจ้าหน้าที่
    # (เราสามารถดึงข้อมูลจากตาราง user ที่ผูกไว้มาโชว์ด้วยได้ เช่น user__username)
    list_display = ('user', 'employee_id', 'position', 'department', 'access_level', 'status')
    
    # สร้างตัวกรองข้อมูลด้านขวามือ เพื่อให้แอดมินคลิกดูเฉพาะคนที่เป็น ACTIVE หรือ PENDING ได้ง่ายๆ
    list_filter = ('status', 'access_level', 'department')
    
    # สร้างช่องค้นหา โดยพิมพ์ค้นหาจากรหัสพนักงาน ตำแหน่ง หรือชื่อยูสเซอร์ได้
    search_fields = ('employee_id', 'position', 'user__username', 'user__first_name')
