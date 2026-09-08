"""
สร้างข้อมูลตัวอย่าง (mock data) ลงฐานข้อมูลที่ DATABASE_URL ชี้ไปตอนนี้
ใช้สำหรับเดโม/พัฒนา — รันซ้ำได้ (เช็คว่ามีอยู่แล้วก็ข้าม ไม่สร้างซ้ำ)

วิธีรัน:
    cd backend
    python seed_mock_data.py
"""
from datetime import datetime, timedelta, timezone

from database import engine, Base, SessionLocal
from models import UnifiedUser, Bicycle, Favorite, PenaltyStrike, LostItem, FavoriteTargetType, PenaltyReason

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def get_or_create_user(username, first_name, last_name, phone, points):
    u = db.query(UnifiedUser).filter(UnifiedUser.username == username).first()
    if u:
        return u
    u = UnifiedUser(username=username, first_name=first_name, last_name=last_name, phone=phone, points=points)
    db.add(u)
    db.flush()
    return u


def get_or_create_bike(bike_code, brand, model, color, status="available"):
    b = db.query(Bicycle).filter(Bicycle.bike_code == bike_code).first()
    if b:
        return b
    b = Bicycle(bike_code=bike_code, brand=brand, model=model, color=color, status=status)
    db.add(b)
    db.flush()
    return b


# ===== ผู้ใช้ (unified_user — ปกติทีม Django เป็นคนสร้างจริง อันนี้จำลองไว้เทส) =====
u1 = get_or_create_user("user001", "สมชาย", "ใจดี", "0810000001", points=12)
u2 = get_or_create_user("user002", "สมหญิง", "รักเรียน", "0810000002", points=8)
u3 = get_or_create_user("user003", "วิชัย", "ขยันเรียน", "0810000003", points=12)

# ===== จักรยาน (bicycle — ปกติทีม Django เป็นคนสร้างจริง) =====
b1 = get_or_create_bike("BIKE001", "Trek", "Mountain", "แดง")
b2 = get_or_create_bike("BIKE002", "Giant", "City", "น้ำเงิน")
b3 = get_or_create_bike("BIKE003", "Merida", "Hybrid", "ดำ", status="maintenance")

db.commit()

# ===== รายการโปรด =====
if db.query(Favorite).count() == 0:
    db.add_all([
        Favorite(user_id=u1.id, target_type=FavoriteTargetType.BICYCLE, bicycle_id=b1.id, nickname="คันโปรดเบอร์ 1"),
        Favorite(user_id=u1.id, target_type=FavoriteTargetType.STATION, station_name="สถานีหน้าหอ"),
        Favorite(user_id=u2.id, target_type=FavoriteTargetType.BICYCLE, bicycle_id=b2.id, nickname="คันประจำ"),
    ])
    db.commit()
    print("✓ เพิ่มรายการโปรดตัวอย่างแล้ว")

# ===== คะแนน/บทลงโทษ (ผสมทั้ง -1 และ +1 ตามเงื่อนไข) =====
if db.query(PenaltyStrike).count() == 0:
    now = datetime.now(timezone.utc)
    db.add_all([
        PenaltyStrike(
            user_id=u2.id, reason=PenaltyReason.LATE_RETURN, penalty_points=1, action="warning",
            description="คืนช้ากว่ากำหนด 30 นาที", completed=True,
            created_at=now - timedelta(days=3),
        ),
        PenaltyStrike(
            user_id=u2.id, reason=PenaltyReason.DAMAGED, penalty_points=1, action="service",
            description="ยางรั่วจากการใช้งานไม่ระมัดระวัง", completed=False,
            created_at=now - timedelta(days=10),
        ),
        PenaltyStrike(
            user_id=u3.id, reason=PenaltyReason.GOOD_BEHAVIOR, penalty_points=1, action="reward",
            description="คืนตรงเวลาและดูแลจักรยานดีต่อเนื่อง", completed=True,
            created_at=now - timedelta(days=1),
        ),
    ])
    db.commit()
    print("✓ เพิ่มคะแนน/บทลงโทษตัวอย่างแล้ว")

# ===== ของหาย (มีทั้งแบบผูกจักรยาน และไม่ผูก) =====
if db.query(LostItem).count() == 0:
    db.add_all([
        LostItem(user_id=u1.id, bicycle_id=b1.id, item_name="กระบอกน้ำ", location="สถานีศูนย์กีฬา", status="lost"),
        LostItem(user_id=u2.id, bicycle_id=None, item_name="กุญแจห้อง", location="ลานจอดจักรยาน", status="lost"),
        LostItem(user_id=u3.id, bicycle_id=b3.id, item_name="หมวกกันน็อค", location="สถานีคณะวิศวะ", status="found"),
    ])
    db.commit()
    print("✓ เพิ่มของหายตัวอย่างแล้ว")

db.close()
print("\nเสร็จแล้ว! ผู้ใช้ตัวอย่าง: user001 (12 แต้ม), user002 (8 แต้ม, 2 บทลงโทษ), user003 (12 แต้ม, 1 พฤติกรรมดี)")
