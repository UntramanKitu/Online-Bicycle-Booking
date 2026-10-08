# Data Mapping — นายชัยอนันต์ (จอง · ปั่นกลุ่ม · แจ้งปัญหา)

> แยกจาก `datamapping.md` — ครอบคลุมเฉพาะงานของชัยอนันต์ตาม `เอกสารหัวข้ออาจารย์.md` §5:
> **Table 1: Reservation & Booking** · **Table 2: Group Ride Bookings** · **Table 3: Support Tickets**
> อัปเดตล่าสุด: 2026-10-08

---

## 1. ขอบเขตงาน (หน้า → Component → Router → ตาราง)

| งาน | Route หน้าเว็บ | Component (frontend) | Router (backend) | ตาราง PostgreSQL |
|---|---|---|---|---|
| Table 1 การจองล่วงหน้า | `/bookings` | `modules/chaianan/pages/BookingsPage.jsx` | `modules/chaianan/reservation_booking/router.py` | `reservation_booking` |
| Table 2 กลุ่มปั่นร่วมกัน | `/group-rides` | `modules/chaianan/pages/GroupRidesPage.jsx` | `modules/chaianan/group_ride_bookings/router.py` | `group_ride`, `group_ride_member` |
| Table 3 รับแจ้งปัญหา | `/support` | `modules/chaianan/pages/TicketsPage.jsx` | `modules/chaianan/support_tickets/router.py` | `support_ticket` |

```
หน้า React (frontend/src/modules/chaianan/pages/*.jsx)
   │  import { api }  ← baseURL `${VITE_API_URL}/api` (cookie session)
   ▼
FastAPI modules/chaianan/* (router.py + business logic)
   ▼
SQLAlchemy Models — models/booking.py (ReservationBooking, SupportTicket)
                     models/group_ride.py (GroupRide, GroupRideMember)
   ▼
PostgreSQL (.env)
```

---

## 2. ตารางสรุป API ต่อหน้า

### 2.1 `/bookings` — BookingsPage.jsx (Table 1)

| ส่วน UI ในหน้า | ข้อมูล/การกระทำ | API | ตาราง |
|---|---|---|---|
| การ์ดจักรยานเลือกจอง (`bikes`) | รายการรถว่าง | `GET /bicycles` | `bicycle` |
| "การจองของฉัน" / "การจองทั้งระบบ" (`myBookings`, `scope`) | รายการจอง | `GET /bookings?user_id={id}` หรือ `GET /bookings` (แอดมิน) | `reservation_booking` |
| สร้างการจอง (เลือกเวลารับรถ) | ฟอร์ม | `POST /bookings` | `reservation_booking` |
| ปุ่ม เลื่อนเวลา | แก้เวลา/ระยะเวลา | `PUT /bookings/{id}` | `reservation_booking` |
| ปุ่ม ยืนยัน (แอดมิน) | เปลี่ยนสถานะ pending→confirmed | `POST /bookings/{id}/confirm?user_id=` | `reservation_booking` |
| ปุ่ม รับรถ | เริ่มยืม (in_progress) | `POST /bookings/{id}/borrow?user_id=` | `reservation_booking` |
| ปุ่ม คืนรถ | จบการยืม (completed) | `POST /bookings/{id}/return?user_id=` | `reservation_booking` |
| ปุ่ม ยกเลิก | ยกเลิก (cancelled) | `POST /bookings/{id}/cancel?user_id=` | `reservation_booking` |
| ล้างประวัติ | ลบรายการ completed/cancelled | `DELETE /bookings/history?user_id=` | `reservation_booking` |
| ปุ่ม ♥ ในการ์ด (FavoriteButton) | ของโมดูลอื่น — แต่ใช้จากหน้านี้ | `POST /favorites`, `DELETE /favorites/{id}` | `favorite` |
| ปุ่ม "แจ้งปัญหา" (modal) | ฟอร์มแจ้งปัญหา → **Table 3** | `POST /tickets` | `support_ticket` |
| ปุ่ม "แจ้งของหาย" (LostItemModal) | ของโมดูลเอกพล | `POST /lost-items` | `lost_item` |
| "การแจ้งของหายของฉัน" (LostItemHistory) | ลิงก์ไป `/profile?tab=lost` | `GET /lost-items/user/{id}` | `lost_item` |
| popup ให้คะแนนหลังคืนรถ (Stars) | ของโมดูลณธิดา | `POST /reviews`, `POST /upload` | `reviews` |
| แจ้งเตือนก่อนรับรถ 15 นาที (หน้าเช็คเอง) | แสดงแถวแจ้งเตือน (ไม่ยิง API — server สร้าง notification ให้) | — | `notifications` |

### 2.2 `/group-rides` — GroupRidesPage.jsx (Table 2)

| ส่วน UI ในหน้า | ข้อมูล/การกระทำ | API | ตาราง |
|---|---|---|---|
| รายการกลุ่มรอบตัว (status=open) + กลุ่มของฉัน (`groups`, `myGroups`) | ค้นหา/ดูกลุ่ม | `GET /group-rides?status=open` · `GET /group-rides?user_id={id}` · `GET /group-rides` (ทั้งหมด) | `group_ride` |
| ดูรายละเอียดกลุ่ม (modal/detail) | รายละเอียด + รายชื่อสมาชิก | `GET /group-rides/{id}` | `group_ride`, `group_ride_member` |
| สร้างกลุ่มใหม่ (ชื่อ, จุดหมาย, เวลานัด, โควตา) | Create | `POST /group-rides` | `group_ride` + `group_ride_member` (หัวหน้า) |
| ปุ่ม "เข้าร่วมกลุ่ม" | +1 current_members, เต็ม → full | `POST /group-rides/{id}/join` `{user_id}` | `group_ride`, `group_ride_member` |
| ปุ่ม "ออกจากกลุ่ม" | -1 คืนโควตา (left_at) | `POST /group-rides/{id}/leave` `{user_id}` | `group_ride`, `group_ride_member` |
| แก้ไขกลุ่ม (หัวหน้า: เวลา/จุดหมาย) | Update | `PUT /group-rides/{id}?user_id=` | `group_ride` |
| ยกเลิกกลุ่ม (หัวหน้า) | status→cancelled | `DELETE /group-rides/{id}?user_id=` | `group_ride` |
| ล้างกลุ่มที่ยกเลิกแล้ว | ลบแถว cancelled | `DELETE /group-rides/cancelled` | `group_ride` |

### 2.3 `/support` — TicketsPage.jsx (Table 3)

| ส่วน UI ในหน้า | ข้อมูล/การกระทำ | API | ตาราง |
|---|---|---|---|
| ฟอร์มแจ้งปัญหาใหม่ (หัวข้อ, รายละเอียด, หมวด, ความสำคัญ) | Create | `POST /tickets` | `support_ticket` |
| รายการคำร้องของฉัน (มุมมองผู้ใช้) | Read (ของตัวเอง) | `GET /tickets?user_id={id}` | `support_ticket` |
| มุมมองแอดมิน `scope=all` | Read ทุกคน + แก้สถานะ/ลบ | `GET /tickets`, `PATCH /admin/tickets/{id}/status`, `DELETE /admin/tickets/{id}`, `DELETE /admin/tickets?status=` | `support_ticket` |
| ปุ่มลบคำร้องของตัวเอง | Delete | `DELETE /tickets/{id}?user_id=` | `support_ticket` |

> ปุ่ม "แจ้งปัญหา" ในหน้า `/bookings` และแท็บ 🎫 ในโปรไฟล์ก็เขียนลงตาราง `support_ticket` เหมือนกัน (คนละหน้าคนละ component แต่โต๊ะเดียว)


---

## 3. ตารางในฐานข้อมูลของชัยอนันต์ (Model → คอลัมน์สำคัญ)

| ตาราง | Model | คอลัมน์สำคัญ | ค่า status ที่เป็นไปได้ |
|---|---|---|---|
| `reservation_booking` | `models/booking.py` → `ReservationBooking` | `id, user_id, bicycle_id, booking_type (advance_reservation/walk_in), start_time, end_time, status, pickup_location, return_location, note, checked_out_at, checked_in_at, pickup_reminded_at, overdue_notified_at, created_at` | `pending → confirmed → in_progress → completed` / `cancelled` / `no_show` |
| `group_ride` | `models/group_ride.py` → `GroupRide` | `id, created_by (หัวหน้า), name, destination, meetup_location, meetup_time, max_members, current_members, created_at` | `open → full` / `cancelled` / `completed` |
| `group_ride_member` | `models/group_ride.py` → `GroupRideMember` | `group_ride_id, user_id, role, joined_at, left_at` (unique: group+user) | `leader` / `member` |
| `support_ticket` | `models/booking.py` → `SupportTicket` | `id, user_id, assigned_to, subject, description, category, priority, status, resolution_notes, resolved_at, created_at` | `open → in_progress → resolved / closed / reopened` · category: `bicycle_issue/account_issue/booking_issue/other` · priority: `low/normal/high/urgent` |

---

## 4. หน้าของชัยอนันต์ไปใช้ข้อมูลของโมดูลอื่น (รองรับ)

| หน้า | ส่วนที่ไปใช้ของคนอื่น | API | ตาราง (เจ้าของ) |
|---|---|---|---|
| `/bookings` | การ์ดรถ | `GET /bicycles` | `bicycle` (ปิยะพงษ์ §1) |
| `/bookings` | ♥ รายการโปรด | `POST/DELETE /favorites` | `favorite` (เอกพล) |
| `/bookings` | แจ้งของหาย + ประวัติของฉัน | `POST /lost-items`, `GET /lost-items/user/{id}` | `lost_item` (เอกพล) |
| `/bookings` | popup ให้คะแนนหลังคืนรถ | `POST /reviews`, `POST /upload` | `reviews`, ไฟล์อัปโหลด (ณธิดา) |
| `/bookings` | แจ้งซ่อม (ถ้ามีใน flow) | `POST /maintenance-reports` | `maintenance_reports` (ปิยะพงษ์ §1) |
| `/support`, `/bookings` | ชื่อผู้แจ้ง/รายชื่อ user | `GET /auth/me`, `GET /users` (context) | `accounts_unifieduser` |

---

## 5. Backend ที่เกี่ยวข้องกับงานชัยอนันต์

| ระบบ | ไฟล์ | เกี่ยวข้องอย่างไร |
|---|---|---|
| แจ้งเตือนก่อนรับรถ/คืนรถ (FR3.6) | `modules/nathida/reminders.py` | อ่าน `reservation_booking` (ใกล้ถึงเวลา/คืนรถเกิน) → สร้างแถวใน `notifications` กันซ้ำด้วย `pickup_reminded_at` / `overdue_notified_at` |
| Seed การจอง/รถตั้งต้น | `app/seed/seed_bookings.py`, `seed_bicycles.py` | เติมข้อมูล test ใน `reservation_booking` / `bicycle` |
| Router ที่ register ใน `main.py` | `app.include_router(reservation_booking / group_ride / support_ticket, prefix="/api")` | path จริง = `/api/bookings`, `/api/group-rides`, `/api/tickets` (+ `/api/admin/tickets*`) |

---

## 6. หมายเหตุ

- หน้า `/bookings` เป็นหน้า "ศูนย์กลาง" ของชัยอนันต์ — เรียก API ของโมดูลอื่นด้วย (ข้อ 4) แต่ **ตารางหลักของตัวเองมี 4 ตัว**: `reservation_booking`, `group_ride`, `group_ride_member`, `support_ticket`
- `support_ticket` ถูกเขียนจาก 3 ทาง: หน้า `/support`, ปุ่มแจ้งปัญหาใน `/bookings`, แท็บ 🎫 ในโปรไฟล์
- ไฟล์ที่ห้ามพลาด: `BookingsPage.jsx`, `GroupRidesPage.jsx`, `TicketsPage.jsx` (frontend) · `reservation_booking/router.py`, `group_ride_bookings/router.py`, `support_tickets/router.py` (backend)
- อ่านภาพรวมทั้งระบบต่อที่ `datamapping.md`

