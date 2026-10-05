"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# =========================================================================
# ระบบเส้นทางหลักของโปรเจกต (Main Routing - config/urls.py)
# =========================================================================
# ไฟล์นี้เปรียบเสมือน "ป้ายบอกทางหน้าหมู่บ้าน" เวลามีคนเข้าเว็บมา มันจะมาอ่านไฟล์นี้เป็นที่แรก
# เพื่อเช็คว่าลิงก์ที่พิมพ์มา ควรจะส่งไปหาโฟลเดอร์ไหน (App ไหน) ให้เป็นคนจัดการต่อ

urlpatterns = [
    # 1. เส้นทางสำหรับหน้าจัดการฐานข้อมูล (ระบบหลังบ้านที่มีมาให้แต่เกิดของ Django)
    # ถ้าเข้าเว็บด้วย http://.../admin/ ให้ไปที่ระบบ admin
    path('admin/', admin.site.urls), 
    
    # 2. เชื่อมโยง URL เข้ากับระบบบัญชี (Accounts App)
    # ถ้า URL ขึ้นต้นด้วย /accounts/... (เช่น /accounts/login) 
    # ระบบจะโยนหน้าที่ไปให้ไฟล์ urls.py ในโฟลเดอร์ accounts จัดการต่อ
    path('accounts/', include('accounts.urls')), 
    
    # 3. เชื่อมโยง URL เข้ากับระบบบุคลากร (Staff App)
    # สำหรับการจัดการรายชื่อพนักงาน หรือการขอสิทธิ์
    path('staff/', include('staff.urls')),
    
    # 4. เชื่อมโยง URL เข้ากับระบบประกาศข่าวสาร (Announcements App)
    path('announcements/', include('announcements.urls')),
    
    # 5. หน้าแรกสุด (Homepage)
    # path แบบเว้นว่าง '' หมายถึงถ้าพิมพ์แค่ชื่อเว็บ http://.../ เปล่าๆ ไม่ต่อท้ายอะไรเลย
    # ให้วิ่งไปให้ระบบ core (core.urls) จัดการวาดหน้าแรกให้
    path('', include('core.urls')), 
]

# =========================================================================
# การตั้งค่าสำหรับโชว์รูปภาพในโหมด Development
# =========================================================================
# โค้ดส่วนนี้สำคัญมาก! ถ้าเราเปิดโหมด DEBUG = True (กำลังเขียนโค้ดในเครื่องตัวเอง)
# โค้ดนี้จะสั่งให้ Django ยอมแสดงรูปภาพและไฟล์ต่างๆ ที่ผู้ใช้อัปโหลดเข้ามา (Media files)
# (ถ้าไม่มีโค้ด 2 บรรทัดนี้ อัปโหลดรูปได้ แต่พอเปิดดูรูปมันจะขึ้น 404 Not Found)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)