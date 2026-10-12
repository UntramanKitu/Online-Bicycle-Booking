"""สคริปต์สร้างข้อมูลตัวอย่าง (mock data) สำหรับ BikeShare

รันด้วย:  .venv\\Scripts\\python.exe seed_mock.py
- สร้างบัญชีตัวอย่าง (แอดมิน / เจ้าหน้าที่ / นักศึกษา)
- สร้างจักรยานตัวอย่างหลายคัน
- สร้างรายการแจ้งซ่อมตัวอย่าง
- สร้างหมวดหมู่ + ประกาศข่าวสารตัวอย่าง
- สร้างเจ้าหน้าที่ (อนุมัติแล้ว + รออนุมัติ)
"""
import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import transaction  # noqa: E402
from django.utils import timezone  # noqa: E402

from core.models import Bicycle, Maintenance  # noqa: E402
from announcements.models import (  # noqa: E402
    AnnouncementCategory,
    CampusAnnouncement,
)
from staff.models import StaffProfile  # noqa: E402

User = get_user_model()


def ensure_user(username, password, first, last, email, superuser=False, staff=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first,
            "last_name": last,
            "email": email,
            "is_superuser": superuser,
            "is_staff": staff or superuser,
        },
    )
    user.set_password(password)
    user.save()
    if created:
        print(f"  + user {username} ({user.role})")
    return user


BIKES = [
    # code, brand, model, color, location, status, rides, price
    ("N-BIKE-001", "Giant", "Escape 3", "ดำ", "หน้าตึกอธิการบดี", Bicycle.Status.AVAILABLE, 42, 14500),
    ("N-BIKE-002", "Trek", "FX 2", "ขาว", "ประตูวิศวกรรม", Bicycle.Status.AVAILABLE, 18, 18000),
    ("E-BIKE-001", "Aventon", "Pace 500", "เทา", "ตึกวิทยาศาสตร์", Bicycle.Status.IN_USE, 63, 32000),
    ("E-BIKE-002", "Fiido", "D11", "เขียว", "ห้องสมุดกลาง", Bicycle.Status.AVAILABLE, 27, 21000),
    ("P-BIKE-001", "Dahon", "Mariner D8", "น้ำเงิน", "โรงอาหาร", Bicycle.Status.AVAILABLE, 9, 16000),
    ("T-BIKE-001", "Merida", "Big Seven", "ส้ม", "ค่ายกีฬา", Bicycle.Status.UNDER_MAINTENANCE, 55, 19000),
    ("N-BIKE-003", "Giant", "ATX 27.5", "แดง", "หอพักนิสิต A", Bicycle.Status.RETIRED, 120, 13000),
    ("N-BIKE-004", "Cannondale", "Quick 6", "ฟ้า", "คณะบริหารธุรกิจ", Bicycle.Status.AVAILABLE, 35, 17500),
]


def seed_bikes():
    made = 0
    for code, brand, model, color, loc, status, rides, price in BIKES:
        _, created = Bicycle.objects.get_or_create(
            bike_code=code,
            defaults={
                "brand": brand,
                "model": model,
                "color": color,
                "current_location": loc,
                "status": status,
                "total_rides": rides,
                "purchase_price": Decimal(price),
                "purchase_date": date.today() - timedelta(days=365),
                "qr_code": f"QR-{code}",
            },
        )
        if created:
            made += 1
    print(f"  + bicycles: created {made} (total {Bicycle.objects.count()})")

def seed_maintenance(reporter):
    if Maintenance.objects.exists():
        print("  - maintenance already exists, skip")
        return
    data = [
        ("T-BIKE-001", Maintenance.MaintenanceType.REPAIR, "เปลี่ยนยางล้อหน้า เพราะสึกเรียบ", Maintenance.Status.IN_PROGRESS, Decimal(450)),
        ("E-BIKE-001", Maintenance.MaintenanceType.ROUTINE_CHECK, "ตรวจเช็คแบตและระบบไฟ", Maintenance.Status.COMPLETED, Decimal(0)),
        ("N-BIKE-002", Maintenance.MaintenanceType.PART_REPLACEMENT, "เปลี่ยนเบรกหน้า", Maintenance.Status.PENDING, Decimal(320)),
    ]
    made = 0
    for code, mtype, desc, status, cost in data:
        try:
            bike = Bicycle.objects.get(bike_code=code)
        except Bicycle.DoesNotExist:
            continue
        Maintenance.objects.create(
            bicycle=bike,
            reported_by=reporter,
            type=mtype,
            description=desc,
            status=status,
            cost=cost,
            start_date=date.today() - timedelta(days=3),
            end_date=date.today() if status == Maintenance.Status.COMPLETED else None,
        )
        made += 1
    print(f"  + maintenance: created {made}")


def seed_announcements(admin):
    cats = [
        ("ข่าวทุนการศึกษา", True),
        ("กิจกรรมนักศึกษา", True),
        ("ประกาศรับสมัครงาน", True),
    ]
    cat_objs = []
    for name, active in cats:
        c, _ = AnnouncementCategory.objects.get_or_create(
            name=name, defaults={"is_active": active}
        )
        cat_objs.append(c)
    if CampusAnnouncement.objects.exists():
        print("  - announcements already exist, skip")
        return
    now = timezone.now()
    anns = [
        ("เปิดรับสมัครทุนการศึกษาร่วมระดับมหาวิทยาลัย",
         "มหาวิทยาลัยเปิดรับสมัครทุนการศึกษาสำหรับนักศึกษาทุกระดับ ยื่นเอกสารที่กองกิจการนักศึกษา ภายใน 30 วัน",
         cat_objs[0], CampusAnnouncement.Priority.HIGH, CampusAnnouncement.Status.PUBLISHED, CampusAnnouncement.TargetAudience.ALL, True),
        ("กิจกรรม BikeShare ประจำเดือน มาร่วมกัน!",
         "ร่วมปั่นจักรยานฟรีรอบมหาวิทยาลัย จุดรวมตัวหน้าหอสมุดกลาง เวลา 08:00 น.",
         cat_objs[1], CampusAnnouncement.Priority.NORMAL, CampusAnnouncement.Status.PUBLISHED, CampusAnnouncement.TargetAudience.STUDENT, False),
        ("รับสมัครพนักงานชั่วคราว แผนกบุคคล",
         "ตำแหน่งผู้ช่วยงานธุรการ เงินเดือน 15,000 บาท สนใจติดต่อฝ่ายบุคคลภายใน 7 วัน",
         cat_objs[2], CampusAnnouncement.Priority.URGENT, CampusAnnouncement.Status.PUBLISHED, CampusAnnouncement.TargetAudience.ALL, False),
        ("ประกาศแจ้งปิดปรับปรุงระบบชั่วคราว",
         "ระบบ BikeShare จะปิดปรับปรุงวันเสาร์ 00:00 - 06:00 น. เพื่ออัปเกรดเซิร์ฟเวอร์",
         cat_objs[1], CampusAnnouncement.Priority.NORMAL, CampusAnnouncement.Status.DRAFT, CampusAnnouncement.TargetAudience.ALL, False),
    ]
    made = 0
    for title, content, cat, pri, status, aud, pinned in anns:
        CampusAnnouncement.objects.create(
            title=title,
            content=content,
            category=cat,
            priority=pri,
            status=status,
            target_audience=aud,
            is_pinned=pinned,
            publish_at=now if status == CampusAnnouncement.Status.PUBLISHED else now + timedelta(days=7),
            created_by=admin,
            updated_by=admin,
        )
        made += 1
    print(f"  + announcements: created {made} (categories {AnnouncementCategory.objects.count()})")


def seed_staff():
    mgr, _ = User.objects.get_or_create(username="manager1", defaults={
        "first_name": "สมชาย", "last_name": "จัดการดี", "email": "manager@bike.ac.th",
    })
    mgr.set_password("manager1234")
    mgr.save()
    StaffProfile.objects.get_or_create(
        user=mgr,
        defaults={
            "employee_id": "EMP1001",
            "position": "เจ้าหน้าที่ประชาสัมพันธ์",
            "department": "ฝ่ายประชาสัมพันธ์",
            "access_level": StaffProfile.AccessLevel.MANAGER,
            "status": StaffProfile.Status.ACTIVE,
            "hire_date": date.today() - timedelta(days=200),
        },
    )
    pending, _ = User.objects.get_or_create(username="student_pending", defaults={
        "first_name": "วิชาการ", "last_name": "รออนุมัติ", "email": "pending@bike.ac.th",
    })
    pending.set_password("student1234")
    pending.save()
    StaffProfile.objects.get_or_create(
        user=pending,
        defaults={
            "employee_id": "EMP2001",
            "position": "นักวิชาการคอมพิวเตอร์",
            "department": "กองเทคโนโลยี",
            "access_level": StaffProfile.AccessLevel.BASIC,
            "status": StaffProfile.Status.PENDING,
        },
    )
    ensure_user("student1", "student1234", "นัก", "เรียนดี", "student@bike.ac.th")
    print(f"  + staff profiles: {StaffProfile.objects.count()}")


@transaction.atomic
def main():
    print("Seeding mock data for BikeShare ...")
    ensure_user("admin", "admin1234", "ผู้ดูแล", "ระบบ", "admin@bike.ac.th",
                superuser=True, staff=True)
    admin = User.objects.get(username="admin")
    seed_bikes()
    seed_maintenance(admin)
    seed_announcements(admin)
    seed_staff()
    print("Done. Login accounts:")
    print("  admin / admin1234              -> admin")
    print("  manager1 / manager1234         -> manager")
    print("  student1 / student1234         -> student")
    print("  student_pending / student1234  -> (requesting staff access)")


if __name__ == "__main__":
    main()

