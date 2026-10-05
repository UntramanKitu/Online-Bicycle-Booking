from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.decorators import login_required

# =========================================================================
# โซน 1: ฟังก์ชันช่วยตรวจสอบสิทธิ์เบื้องต้น (Helper Functions)
# =========================================================================

# ฟังก์ชันนี้เช็คว่า ผู้ใช้งานที่ล็อกอินเข้ามา เป็น "ผู้ดูแลระบบ (ADMIN)" หรือไม่?
def is_announcement_admin(user):
    # คืนค่าเป็น True ถ้าผู้ใช้ล็อกอินแล้ว (is_authenticated) 
    # และค่าสิทธิ์ในตัวแปร 'role' ของเขา เท่ากับ 'ADMIN'
    # (ใช้ getattr เพื่อป้องกัน Error ในกรณีที่ผู้ใช้คนนั้นบังเอิญไม่มีตัวแปร role)
    return user.is_authenticated and getattr(user, 'role', '') == 'ADMIN'

# ฟังก์ชันนี้เช็คว่า ผู้ใช้งานที่ล็อกอินเข้ามา เป็น "ระดับเจ้าหน้าที่ขึ้นไป" หรือไม่?
def is_announcement_staff(user):
    # คืนค่าเป็น True ถ้าล็อกอินแล้ว และสิทธิ์ (role) เป็น 'ADMIN' หรือ 'MANAGER'
    return user.is_authenticated and getattr(user, 'role', '') in ['ADMIN', 'MANAGER']


# =========================================================================
# โซน 2: ฟังก์ชันสำหรับล็อคหน้าเว็บ (Decorators)
# =========================================================================
# Decorator คือตัวที่เอาไปแปะไว้บนหัวฟังก์ชันหน้าเว็บต่างๆ (เช่น @staff_required)
# ทำหน้าที่เป็น "ยามเฝ้าประตู" คอยเช็คสิทธิ์ก่อนจะยอมให้เปิดหน้าเว็บนั้นๆ ได้

# 1. ยามเฝ้าประตูสำหรับหน้าเว็บที่ "เจ้าหน้าที่หรือแอดมิน" เท่านั้นที่เข้าได้
def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # ขั้นที่ 1: เช็คก่อนเลยว่าล็อกอินหรือยัง?
        if not request.user.is_authenticated:
            # ถ้ายังไม่ล็อกอิน ให้ไล่ไปหน้าล็อกอินก่อน 
            # พร้อมแนบ path ปัจจุบันไปด้วย เพื่อที่พอล็อกอินเสร็จจะได้เด้งกลับมาหน้านี้ถูก
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
            
        # ขั้นที่ 2: ถ้าล็อกอินแล้ว ลองเช็คดูซิว่าเป็นเจ้าหน้าที่ไหม? (เรียกใช้ฟังก์ชัน is_announcement_staff)
        if is_announcement_staff(request.user):
            # ถ้าเป็นเจ้าหน้าที่จริง ยอมให้เข้าไปดูหน้าเว็บนั้นได้ (เรียกใช้ view_func)
            return view_func(request, *args, **kwargs)
            
        # ขั้นที่ 3: ถ้าล็อกอินแล้ว แต่เป็นแค่นักศึกษาหรือผู้ใช้ทั่วไป 
        # ให้ขึ้น Error หน้าแดง (PermissionDenied - สิทธิ์ไม่เพียงพอ หรือ 403 Forbidden)
        raise PermissionDenied
    return _wrapped_view

# 2. ยามเฝ้าประตูที่เข้มงวดที่สุด! ต้องเป็น "ผู้ดูแลระบบ (ADMIN)" เท่านั้น
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # ขั้นที่ 1: เช็คว่าล็อกอินยัง? (เหมือนตัวข้างบน)
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
            
        # ขั้นที่ 2: เช็คว่าเป็น ADMIN ไหม? (เรียกใช้ฟังก์ชัน is_announcement_admin)
        if is_announcement_admin(request.user):
            # ถ้าใช่แอดมิน ผ่านเข้าไปได้เลย
            return view_func(request, *args, **kwargs)
            
        # ถ้าไม่ใช่แอดมิน (แม้จะเป็นเจ้าหน้าที่) ก็จะโดนเตะออกหน้า 403 (PermissionDenied)
        raise PermissionDenied
    return _wrapped_view
