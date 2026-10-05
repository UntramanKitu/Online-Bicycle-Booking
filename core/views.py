# core/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# =========================================================================
# ระบบหลังบ้านและหน้าหลักส่วนตัว (Core Views)
# =========================================================================

# @login_required คือ "ยามเฝ้าประตู" ของ Django 
# ทำหน้าที่เช็คว่าคนที่พยายามเปิดหน้านี้ "ล็อกอินหรือยัง?"
# ถ้ายังไม่ล็อกอิน มันจะเตะกลับไปที่หน้าล็อกอินโดยอัตโนมัติ (ตั้งค่าไว้ใน settings.py ลิงก์ไปที่ /accounts/login)
@login_required
def home(request):
    # ฟังก์ชันนี้สั้นๆ ง่ายๆ คือถ้าล็อกอินแล้ว 
    # ก็แค่ให้วาดหน้าเว็บชื่อ 'core/home.html' ส่งไปให้ผู้ใช้ดู (ซึ่งเป็นหน้า Dashboard หลักของคนล็อกอินแล้ว)
    return render(request, 'core/home.html')
