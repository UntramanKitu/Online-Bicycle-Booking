from django.urls import path
from . import views

# =========================================================================
# เส้นทางสำหรับระบบประกาศข่าวสาร (Announcements URLs)
# =========================================================================

# Namespace 'announcements'
app_name = 'announcements'

urlpatterns = [
    # -----------------------------------------------------------
    # Public views (โซนคนทั่วไปและนักศึกษา)
    # -----------------------------------------------------------
    # หน้าแรกของระบบประกาศ (แสดงรายการประกาศทั้งหมด)
    path('', views.announcement_list, name='list'),
    
    # หน้าสำหรับอ่านรายละเอียดประกาศ (รับค่า pk เป็นตัวเลข เช่น /announcements/5/)
    path('<int:pk>/', views.announcement_detail, name='detail'),
    
    # -----------------------------------------------------------
    # Management views (โซนระบบหลังบ้าน สำหรับสร้าง/แก้ประกาศ)
    # -----------------------------------------------------------
    # หน้าแสดงรายการประกาศทั้งหมดในมุมมองของเจ้าหน้าที่ (มีปุ่มสร้าง/แก้/ลบ)
    path('manage/', views.manage_list, name='manage_list'),
    
    # หน้าฟอร์มสำหรับ "สร้าง" ประกาศใหม่
    path('manage/create/', views.manage_create, name='manage_create'),
    
    # หน้าฟอร์มสำหรับ "แก้ไข" ประกาศเดิม
    path('manage/<int:pk>/edit/', views.manage_update, name='manage_update'),
    
    # หน้าสำหรับกดยืนยันการ "ลบ" ประกาศ
    path('manage/<int:pk>/delete/', views.manage_delete, name='manage_delete'),
    
    # -----------------------------------------------------------
    # Category views (โซนจัดการหมวดหมู่ เฉพาะ ADMIN เท่านั้น)
    # -----------------------------------------------------------
    # หน้าแสดงรายชื่อหมวดหมู่ทั้งหมด (เช่น ทุนการศึกษา กิจกรรม)
    path('categories/', views.category_list, name='category_list'),
    
    # หน้าฟอร์มสำหรับสร้างหมวดหมู่ใหม่
    path('categories/create/', views.category_create, name='category_create'),
]
