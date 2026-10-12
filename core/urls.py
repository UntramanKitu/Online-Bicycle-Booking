from django.urls import path
from . import views

# =========================================================================
# เส้นทางสำหรับหน้าแรก + งานปิยะพงษ์ (Bicycle + Maintenance, ported from fluke)
# =========================================================================

# ตั้งชื่อเล่น (Namespace) ให้กับกลุ่ม URL นี้ว่า 'core'
# เวลาระบุใน HTML จะเขียนแบบนี้ได้เลย -> {% url 'core:home' %}
app_name = 'core'

urlpatterns = [
    # เมื่อมีคนเข้าหน้าเว็บหลัก (ไม่มีข้อความต่อท้าย)
    # ให้วิ่งไปทำงานที่ฟังก์ชันชื่อ home ในไฟล์ views.py
    # และตั้งชื่อเส้นทางนี้ว่า 'home'
    path('', views.home, name='home'),

    # Dashboard ภาพรวม (ported from fluke)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Table 2: Bicycle Management
    path('bicycles/', views.bicycles, name='bicycles'),
    path('bicycles/add/', views.bicycle_create, name='bicycle_create'),

    # Table 3: Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance'),
    path('maintenance/add/', views.maintenance_create, name='maintenance_create'),
    path(
        'maintenance/<int:pk>/status/<str:status>/',
        views.maintenance_update_status,
        name='maintenance_update_status',
    ),
]
