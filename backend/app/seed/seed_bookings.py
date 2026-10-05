"""
Mock Data Seeder สำหรับตารางของนายชัยอนันต์
- reservation_booking
- support_ticket
- group_ride + group_ride_member (ตารางกลุ่มปั่นร่วมกัน)
"""

import sys

# กัน App crash เมื่อ stdout/stderr มี encoding ที่พิมพ์ไทย/emoji ไม่ได้ (เช่น Windows cp874)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.crud.booking import (
    create_booking, create_ticket,
)
from app.modules.chaianan.group_ride_bookings.crud import create_group_ride, join_group_ride
from app.schemas.booking import (
    ReservationBookingCreate, SupportTicketCreate,
)
from app.schemas.group_ride import GroupRideCreate


def seed_bookings(db):
    """สร้าง mock data สำหรับ reservation_booking"""
    bookings_data = [
        ReservationBookingCreate(
            user_id=1,
            bicycle_id=1,
            booking_type="advance_reservation",
            start_time=datetime(2026, 7, 25, 8, 0, 0),
            end_time=datetime(2026, 7, 25, 12, 0, 0),
            pickup_location="อาคารเรียนรวม 1",
            return_location="อาคารเรียนรวม 1",
        ),
        ReservationBookingCreate(
            user_id=1,
            bicycle_id=2,
            booking_type="walk_in",
            start_time=datetime(2026, 7, 25, 13, 0, 0),
            end_time=datetime(2026, 7, 25, 15, 0, 0),
            pickup_location="หอสมุดกลาง",
            return_location="หอสมุดกลาง",
        ),
        ReservationBookingCreate(
            user_id=2,
            bicycle_id=1,
            booking_type="advance_reservation",
            start_time=datetime(2026, 7, 26, 9, 0, 0),
            end_time=datetime(2026, 7, 26, 11, 0, 0),
            pickup_location="คณะวิศวกรรมศาสตร์",
            return_location="คณะวิศวกรรมศาสตร์",
        ),
        ReservationBookingCreate(
            user_id=2,
            bicycle_id=3,
            booking_type="walk_in",
            start_time=datetime(2026, 7, 26, 14, 0, 0),
            end_time=datetime(2026, 7, 26, 16, 30, 0),
            pickup_location="สนามกีฬา",
            return_location="สนามกีฬา",
        ),
        ReservationBookingCreate(
            user_id=3,
            bicycle_id=2,
            booking_type="advance_reservation",
            start_time=datetime(2026, 7, 27, 7, 30, 0),
            end_time=datetime(2026, 7, 27, 10, 0, 0),
            pickup_location="หอพักนักศึกษา",
            return_location="หอพักนักศึกษา",
        ),
    ]
    created = []
    for data in bookings_data:
        booking = create_booking(db, data)
        created.append(booking)
        print(f"  ✅ Created booking id={booking.id} (user={data.user_id}, bicycle={data.bicycle_id})")
    return created


def seed_tickets(db):
    """สร้าง mock data สำหรับ support_ticket"""
    tickets_data = [
        SupportTicketCreate(
            user_id=1,
            subject="เบาะจักรยานไม่แน่น",
            description="เบาะจักรยานคันที่ยืมมาหลวมมาก ขันน็อตแล้วก็ยังไม่แน่น กรุณาตรวจสอบให้หน่อยครับ",
            category="bicycle_issue",
            priority="normal",
        ),
        SupportTicketCreate(
            user_id=2,
            subject="ลืมรหัสผ่าน",
            description="เข้าระบบไม่ได้因为我ลืมรหัสผ่าน ขอรีเซ็ตรหัสผ่านด้วยครับ",
            category="account_issue",
            priority="high",
        ),
        SupportTicketCreate(
            user_id=3,
            subject="ขอเลื่อนเวลาคืนจักรยาน",
            description="เนื่องจากติดธุระ ขอเลื่อนเวลาคืนจักรยานจาก 16:00 เป็น 18:00 น. ได้ไหมครับ",
            category="booking_issue",
            priority="normal",
        ),
        SupportTicketCreate(
            user_id=1,
            subject="แจ้งปัญหาจุดรับจักรยาน",
            description="จุดรับจักรยานหน้าหอสมุดมีจักรยานจอดเกะกะทางเดิน เข็นออกลำบาก",
            category="other",
            priority="low",
        ),
        SupportTicketCreate(
            user_id=2,
            subject="ล้อจักรยานแบน",
            description="จักรยานคันที่ยืมมาล้อหลังลมออก ใช้งานไม่ได้ กรุณาส่งคนมาตรวจสอบ",
            category="bicycle_issue",
            priority="urgent",
        ),
    ]
    created = []
    for data in tickets_data:
        ticket = create_ticket(db, data)
        created.append(ticket)
        print(f"  ✅ Created ticket id={ticket.id} (user={data.user_id}, category={data.category})")
    return created


def seed_group_rides(db):
    """สร้าง mock data สำหรับ group_ride (+ group_ride_member)"""
    groups_data = [
        GroupRideCreate(
            created_by=1,
            name="ปั่นเที่ยวหอสมุด หลังเลิกเรียน",
            destination="หอสมุดกลาง",
            meetup_location="ประตูคณะวิทยาศาสตร์",
            meetup_time=datetime(2026, 7, 25, 17, 0, 0),
            max_members=4,
        ),
        GroupRideCreate(
            created_by=2,
            name="ปั่นไปเชียร์บาสสนามกีฬา",
            destination="สนามกีฬา",
            meetup_time=datetime(2026, 7, 26, 14, 0, 0),
            max_members=5,
        ),
        GroupRideCreate(
            created_by=3,
            name="ปั่นกลับหอพัก ตอนค่ำ",
            destination="หอพักนักศึกษา",
            meetup_location="หน้าหอประชุม",
            meetup_time=datetime(2026, 7, 27, 18, 30, 0),
            max_members=2,
        ),
    ]
    created = []
    for data in groups_data:
        group = create_group_ride(db, data)
        created.append(group)
        print(f"  ✅ Created group_ride id={group.id} '{data.name}' (leader={data.created_by})")

    # ให้ user อีกคนเข้าร่วมกลุ่ม 'ปั่นกลับหอพัก ตอนค่ำ' → สมาชิกครบ (2/2) สถานะเปลี่ยนเป็น full
    join_group_ride(db, created[2].id, user_id=1)
    print(f"  ✅ Joined group_ride id={created[2].id} by user 1 (status -> full)")
    return created


def main():
    db = SessionLocal()
    try:
        # Idempotent: ถ้ามี reservation_booking อยู่แล้ว → ข้าม seeding (กัน data ซ้ำ/conflict บน Availability)
        from app.models.booking import ReservationBooking

        if db.query(ReservationBooking).first() is not None:
            print("ℹ️ ข้อมูล reservation_booking มีอยู่แล้ว — ข้าม seeding")
            return

        print("🌱 Seeding data for นายชัยอนันต์...\n")

        print("📌 Seeding reservation_booking...")
        seed_bookings(db)

        print("\n📌 Seeding support_ticket...")
        seed_tickets(db)

        print("\n📌 Seeding group_ride & group_ride_member...")
        seed_group_rides(db)

        print("\n✅ Seed completed successfully!")
    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()