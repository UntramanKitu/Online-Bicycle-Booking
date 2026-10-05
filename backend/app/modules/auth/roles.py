"""สิทธิ์ผู้ใช้ 2 ระดับ: user (ผู้ใช้ทั่วไป) / admin (แอดมิน — เห็นข้อมูลทุกอย่าง)

role ถูกตัดสินจากบัญชีตอนล็อกอิน (ไม่ใช่เลือกตอนกดเข้าสู่ระบบ):
- is_staff / is_superuser ของตาราง accounts_unifieduser (ฝั่ง Django ตั้งไว้) หรือ
- อีเมลอยู่ใน AUTH_ADMIN_EMAILS (คั่นด้วย comma ใน backend/.env)
"""

import os


def admin_emails() -> set[str]:
    """รายชื่ออีเมลแอดมินจาก env — คืนเป็น set ตัวพิมพ์เล็กเพื่อเทียบแบบไม่สน case"""
    raw = os.getenv("AUTH_ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def resolve_role(user) -> str:
    """คืน 'admin' หรือ 'user' — ใช้ทั้ง /auth/me และ /api/users ให้ตรงกัน"""
    if user.is_superuser or user.is_staff:
        return "admin"
    if (user.email or "").strip().lower() in admin_emails():
        return "admin"
    return "user"
