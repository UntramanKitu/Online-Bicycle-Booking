from django.urls import path
from . import views

# =========================================================================
# เส้นทางสำหรับระบบจัดการบุคลากร (Staff URLs)
# =========================================================================

# Namespace 'staff' 
app_name = 'staff'

urlpatterns = [
    # หน้าแสดงรายชื่อบุคลากรทั้งหมด (เช่น เผื่อให้นักศึกษาค้นหาเบอร์โทรอาจารย์)
    path('', views.staff_list, name='staff_list'),
    
    # หน้าส่งแบบฟอร์ม "ขอสิทธิ์เป็นเจ้าหน้าที่" (สำหรับนักศึกษา/ผู้ใช้ทั่วไปที่อยากอัปเกรดตัวเอง)
    path('request-access/', views.request_access, name='request_access'),
    
    # สำหรับแอดมินกด "อนุมัติ" คำขอสิทธิ์ของรหัสพนักงาน (pk) นั้นๆ
    path('<int:pk>/approve/', views.staff_approve, name='staff_approve'),
    
    # สำหรับแอดมินกด "ปฏิเสธ" คำขอสิทธิ์ของรหัสพนักงาน (pk) นั้นๆ
    path('<int:pk>/reject/', views.staff_reject, name='staff_reject'),
    
    # สำหรับแอดมินกด "แก้ไข" ข้อมูลพนักงาน เช่น เลื่อนตำแหน่งให้
    path('<int:pk>/edit/', views.staff_update, name='staff_update'),
    
    # สำหรับแอดมินกด "ลบ" ข้อมูลพนักงานคนนั้นออก
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
]