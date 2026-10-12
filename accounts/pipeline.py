"""
Pipeline สำหรับ social auth (ล็อกอินผ่าน Google)

เหตุผลที่ต้องเขียนเอง:
- โมเดล UnifiedUser สืบทอดจาก AbstractUser ซึ่งช่อง username เป็น unique และบังคับกรอก
  แต่ผู้ใช้ที่ล็อกอินผ่าน Google ไม่ได้กรอก username มาก่อน เราจึงต้อง "สร้าง username
  อัตโนมัติ" จากส่วนหน้าอีเมล (เช่น student@bike.ac.th -> student) และกันซ้ำด้วยตัวเลข
- ตั้ง is_active=True ให้ล็อกอินเข้าใช้ได้ทันที โดยไม่ต้องยืนยันอีเมลซ้ำ
  (Google รับรองความถูกต้องของอีเมลให้เราแล้ว)
"""
import unicodedata
from django.contrib.auth import get_user_model

User = get_user_model()


def _ascii_username_base(details):
    """แปลง username ให้เหลือตัวอักษร/ตัวเลข/._- เท่านั้น"""
    base = (
        details.get("username")
        or (details.get("email") or "user").split("@")[0]
        or "user"
    )
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in base).strip("._-")
    return cleaned[:150] or "user"


def create_or_get_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    หา/สร้างผู้ใช้จากข้อมูล Google (email + ชื่อจริง)
    - ถ้ามี user อยู่ในระบบแล้ว (จับคู่ด้วย email) ให้ใช้คนเดิม
    - ถ้าไม่มี ให้สร้างใหม่พร้อม username อัตโนมัติที่ไม่ซ้ำ
    """
    if user:
        return {"user": user, "is_new": False}

    email = (details.get("email") or "").strip().lower()
    if not email:
        # ไม่มีอีเมลจาก Google -> ไม่สามารถสร้างบัญชีได้
        return None

    # 1) มีอีเมลนี้ในระบบแล้วหรือยัง (ไม่สนตัวพิมพ์เล็ก/ใหญ่)
    existing = User.objects.filter(email__iexact=email).first()
    if existing:
        return {"user": existing, "is_new": False}

    # 2) ยังไม่มี -> สร้างใหม่
    base = _ascii_username_base(details)
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{base}{counter}"

    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=details.get("first_name") or "",
        last_name=details.get("last_name") or "",
    )
    user.is_active = True  # Google รับรองอีเมลอยู่แล้ว ล็อกอินได้ทันที
    user.set_unusable_password()  # ไม่มีรหัสผ่าน เพราะล็อกอินผ่าน Google
    user.save()
    return {"user": user, "is_new": True}
