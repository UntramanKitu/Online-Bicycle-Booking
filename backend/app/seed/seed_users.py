"""Seed ผู้ใช้ทดสอบในตาราง accounts_unifieduser (ตรงกับฝั่ง Django)

สคริปต์นี้ยังไม่ถูกเรียกจาก startup — เรียกด้วยมือเมื่อต้องการเพิ่มผู้ใช้:
    uv run python -m app.seed.seed_users

คอลัมน์ตรงกับ Django AbstractUser ทั้งหมด เพื่อให้ฝั่ง Django อ่านได้ทันที
"""

import sys

# กัน App crash เมื่อ stdout/stderr มี encoding ที่พิมพ์ไทย/emoji ไม่ได้ (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.database import SessionLocal
from app.models.unified_user import UnifiedUser

# ชื่ออ้างอิงจากหัวข้อผู้รับผิดชอบใน docs/Database_Schema_v2 (1).md
USERS = [
    {
        "username": "piyapong.s",
        "email": "piyapong.s@uni.ac.th",
        "first_name": "ปิยะพงษ์",
        "last_name": "สุขใจ",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "weerapong.t",
        "email": "weerapong.t@uni.ac.th",
        "first_name": "วีรพันธ์",
        "last_name": "ทองแท้",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "ekapol.r",
        "email": "ekapol.r@uni.ac.th",
        "first_name": "เอกพล",
        "last_name": "รักเรียน",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "nathiada.k",
        "email": "nathiada.k@uni.ac.th",
        "first_name": "ณธิดา",
        "last_name": "กาญจน์",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "chaiyanan.b",
        "email": "chaiyanan.b@uni.ac.th",
        "first_name": "ชัยอนันต์",
        "last_name": "บุญรังษี",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "bike.officer",
        "email": "bike.officer@uni.ac.th",
        "first_name": "ผู้ดูแล",
        "last_name": "จักรยาน",
        "is_staff": True,
        "is_superuser": False,
        "is_active": True,
    },
]


def main():
    db = SessionLocal()
    try:
        existing = {u.username for u in db.query(UnifiedUser).all()}
        added = 0
        for data in USERS:
            if data["username"] in existing:
                continue
            # password ว่าง = บัญชี OAuth ไม่ให้ล็อกอินด้วยรหัสผ่าน (ตรงพฤติกรรม Django unusable password)
            db.add(UnifiedUser(password="", **data))
            added += 1
        db.commit()
        if added:
            print(f"🌱 Seeded users: +{added}")
        else:
            print("ℹ️ Users มีอยู่แล้ว — ข้าม seeding")
    except Exception as e:
        print(f"❌ Seed users failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
