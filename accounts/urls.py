from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import LoginForm
from . import views

# =========================================================================
# เส้นทางสำหรับระบบบัญชี (Accounts URLs)
# =========================================================================

# Namespace 'accounts' เพื่อใช้ใน HTML เช่น {% url 'accounts:login' %}
app_name = 'accounts'

urlpatterns = [
    # 1. หน้าเข้าสู่ระบบ (/accounts/login/)
    # เราใช้ LoginView ของ Django ที่มีมาให้สำเร็จรูปเลย (ไม่ต้องเขียน logic เองให้เหนื่อย)
    # แต่เราสั่งให้มันเปลี่ยนมาใช้หน้าตา HTML ของเรา (accounts/login.html) 
    # และใช้แบบฟอร์มหน้าตาที่เราตกแต่งเอง (LoginForm) แทนของเดิมที่จืดชืด
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LoginForm
    ), name='login'),
    
    # 2. หน้าออกจากระบบ (/accounts/logout/)
    # ใช้ของสำเร็จรูปของ Django เช่นกัน พอกดปุ่มออกระบบ มันจะทำลาย Session ให้ทันที
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 3. หน้าสมัครสมาชิกใหม่ (/accounts/register/)
    # อันนี้เราเขียนระบบเอง จึงวิ่งไปเรียกฟังก์ชัน register ในไฟล์ views.py
    path('register/', views.register, name='register'),
    
    # 4. ตัวกลางสำหรับคัดแยกเส้นทางหลังล็อกอิน (/accounts/redirect/)
    # พอผู้ใช้ล็อกอินผ่าน ระบบจะเด้งมาหน้านี้แบบเสี้ยววินาที เพื่อให้ฟังก์ชัน role_redirect
    # เป็นคนตัดสินใจว่า ถ้าเป็นนักศึกษาให้เด้งไปหน้าแรก แต่ถ้าเป็นแอดมินให้เด้งไปหลังบ้าน
    path('redirect/', views.role_redirect, name='role_redirect'),
]