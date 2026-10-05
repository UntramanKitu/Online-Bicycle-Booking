from django.contrib import admin
from .models import UnifiedUser

# =========================================================================
# ระบบหลังบ้านสำหรับบัญชีผู้ใช้ (Accounts Admin)
# =========================================================================
# ไฟล์ admin.py นี้ใช้สำหรับตั้งค่าว่า "เวลาผู้ดูแลระบบล็อกอินเข้าหน้าเว็บ /admin"
# เขาจะเห็นหน้าตาการจัดการข้อมูลตารางต่างๆ เป็นอย่างไรบ้าง

# @admin.register คือการสั่งให้ Django นำโมเดล UnifiedUser ไปแสดงในหน้าหลังบ้าน
@admin.register(UnifiedUser)
class UnifiedUserAdmin(admin.ModelAdmin):
    # list_display คือการตั้งค่าว่าใน "หน้ารายการผู้ใช้" จะให้โชว์คอลัมน์อะไรบ้าง
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'role')
    
    # list_filter คือการสร้าง "กล่องตัวกรอง" ด้านขวามือ ให้แอดมินกดกรองข้อมูลได้ง่ายๆ
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    
    # search_fields คือการสร้าง "ช่องค้นหา" โดยสามารถพิมพ์ค้นหาจาก username, first_name หรือ email ได้เลย
    search_fields = ('username', 'first_name', 'last_name', 'email')
