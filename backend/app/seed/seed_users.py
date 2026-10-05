import sys

# กัน App crash เมื่อ stdout/stderr มี encoding ที่พิมพ์ไทย/emoji ไม่ได้ (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.database import SessionLocal
from app.models.unified_user import UnifiedUser

USERS = [
    {
        "id": 1,
        "username": "somchai.j",
        "password_hash": "hashed-demo",
        "email": "somchai.j@uni.ac.th",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "student_id": "67114540101",
        "faculty": "วิทยาศาสตร์",
        "department": "วิทยาการคอมพิวเตอร์",
        "phone": "081-111-0001",
        "role": "student",
        "status": "active",
    },
    {
        "id": 2,
        "username": "nathiada.k",
        "password_hash": "hashed-demo",
        "email": "nathiada.k@uni.ac.th",
        "first_name": "ณธিদा",
        "last_name": "गाहवा",
        "student_id": "67114540102",
        "faculty": "วิศวกรรมคอมพิวเตอร์",
        "department": "ระบบสารสนเทศ",
        "phone": "081-111-0002",
        "role": "student",
        "status": "active",
    },
    {
        "id": 3,
        "username": "ekapol.r",
        "password_hash": "hashed-demo",
        "email": "ekapol.r@uni.ac.th",
        "first_name": "একপল",
        "last_name": "রাকরেয়িং",
        "student_id": "67114540103",
        "faculty": "วิศวกรรมคอม্পিউটার",
        "department": "নেটওয়ার্ক",
        "phone": "081-111-0003",
        "role": "student",
        "status": "active",
    },
    {
        "id": 4,
        "username": "chaiyanan.b",
        "password_hash": "hashed-demo",
        "email": "chaiyanan.b@uni.ac.th",
        "first_name": "চৈয়ানন্ত",
        "last_name": "বুয়রেণ্গশ্রী",
        "student_id": "67114540104",
        "faculty": "วิশেৱकম্পিউটার",
        "department": "সফটওয়্যার ইঞ্জিনিয়ারিং",
        "phone": "081-111-0004",
        "role": "student",
        "status": "active",
    },
    {
        "id": 5,
        "username": "officer.bike",
        "password_hash": "hashed-demo",
        "email": "officer.bike@uni.ac.th",
        "first_name": "ン色",
        "last_name": "નિયંત્રક",
        "student_id": None,
        "faculty": "สำนักงานบริการ",
        "department": "จัดการจักรยาน",
        "phone": "081-111-0005",
        "role": "officer",
        "status": "active",
    },
]


def main():
    db = SessionLocal()
    try:
        existing = {u.id for u in db.query(UnifiedUser).all()}
        added = 0
        for data in USERS:
            if data["id"] in existing:
                continue
            db.add(UnifiedUser(**data))
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