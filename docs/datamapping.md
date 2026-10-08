# Data Mapping — ข้อมูลแต่ละชิ้นมาจากไหน แสดงที่ไหน

> เอกสารนี้ไล่จาก **หน้า UI → API ที่เรียก → Router ฝั่ง backend → ตาราง PostgreSQL**
> อัปเดตล่าสุด: 2026-10-08

---

## 1. ภาพรวม Flow ข้อมูล

```
หน้า React (frontend/src/...)
   │  import { api } from 'api.js'   ← axios baseURL = `${VITE_API_URL}/api` (cookie session / withCredentials)
   ▼
FastAPI (backend/app/main.py → include_router)
   │  routers/ และ modules/* (path + business logic)
   ▼
SQLAlchemy Models (backend/app/models/*.py)
   ▼
PostgreSQL (อ่านค่าจาก .env — DB_USER/DB_HOST/DB_NAME ฯลฯ, รองรับ Supabase SSL)
```

- **ตารางผู้ใช้กลาง**: `accounts_unifieduser` (mirror ของ Django Monolith — ฝั่งนี้อ่าน/patch บางส่วนเท่านั้น)
- **ไฟล์รูป**: `POST /api/upload` → `backend/app/routers/uploads.py` → เก็บไฟล์แล้วคืน path `/api/uploads/...` → frontend แปลงด้วย `assetUrl()` ใน `api.js`

---

## 2. ตารางสรุปใหญ่: หน้า → หน้าที่แสดงอะไร → API → ตาราง

| Route | หน้า Component | API ที่เรียก (axios) | Backend Router | ตาราง |
|---|---|---|---|---|
| `/login` | `modules/auth/LoginPage.jsx` | `GET /auth/google/login` (ลิงก์ OAuth, ไม่ใช่ fetch) | `modules/auth/router.py` | `accounts_unifieduser` |
| ทุกหน้า | `context/CurrentUserContext.jsx` | `GET /auth/me`, `GET /users`, `GET /notifications/user/{id}` | `auth/router.py`, `routers/user.py`, `nathida/notification.py` | `accounts_unifieduser`, `notifications` |
| ทุกหน้า (header) | `components/Layout.jsx` | `POST /auth/logout`, `PATCH /notifications/{id}/read`, `DELETE /notifications/user/{id}/read` | `auth/router.py`, `nathida/notification.py` | `accounts_unifieduser`, `notifications` |
| `/` `/home` | `pages/HomePage.jsx` | **ไม่เรียก API** (การ์ดเมนูเป็น static ในไฟล์) | — | — |
| `/bookings` | `modules/chaianan/pages/BookingsPage.jsx` | `GET/POST/PUT/DELETE /bookings`, `POST /bookings/{id}/{borrow\|return\|cancel\|confirm}`, `DELETE /bookings/history`, `GET /bicycles`, `GET /lost-items/user/{id}`, `POST /lost-items`, `POST /reviews`, `POST /maintenance-reports`, `POST /upload` | `chaianan/reservation_booking/router.py`, `routers/bicycle.py`, `eakapol/lost_items.py`, `nathida/review.py`, `nathida/maintenance.py`, `routers/uploads.py` | `reservation_booking`, `bicycle`, `lost_item`, `reviews`, `maintenance_reports` |
| `/group-rides` | `modules/chaianan/pages/GroupRidesPage.jsx` | `GET/POST/PUT/DELETE /group-rides`, `GET /group-rides/{id}`, `POST /group-rides/{id}/join\|leave`, `DELETE /group-rides/cancelled` | `chaianan/group_ride_bookings/router.py` | `group_ride`, `group_ride_member` |
| `/support` | `modules/chaianan/pages/TicketsPage.jsx` | `GET /tickets` (admin เห็นทุกคน, ไม่งั้น `?user_id=`), `POST /tickets`, `DELETE /tickets/{id}`, `PATCH /admin/tickets/{id}/status`, `DELETE /admin/tickets[/{id}]` | `chaianan/support_tickets/router.py` | `support_ticket` |
| `/notifications` | `modules/nathida/pages/NotificationsPage.jsx` | `GET /notifications` (admin) หรือ `GET /notifications/user/{id}`, `PATCH /notifications/{id}/read`, `DELETE /notifications/user/{id}/read` | `nathida/notification.py` | `notifications` |
| `/maintenance` | `modules/nathida/pages/MaintenancePage.jsx` | `GET /maintenance-reports` (admin) หรือ `/user/{id}`, `POST /maintenance-reports`, `POST /upload`, `GET /bicycles` | `nathida/maintenance.py`, `routers/uploads.py`, `routers/bicycle.py` | `maintenance_reports`, `bicycle` |
| `/reviews` | `modules/nathida/pages/ReviewsPage.jsx` | `GET /reviews/bicycle/{id}`, `GET /reviews/bicycle/{id}/summary`, `POST /reviews`, `DELETE /reviews/{id}`, `GET /bicycles` | `nathida/review.py`, `routers/bicycle.py` | `reviews`, `bicycle` |
| `/scores` | `modules/akeapon/pages/ScoresPage.jsx` | `GET /penalties/user/{id}` | `eakapol/penalties.py` | `penalty_strike` |
| `/favorites` | `modules/akeapon/pages/FavoritesPage.jsx` | `GET /favorites/user/{id}`, `PUT /favorites/{id}` (ชื่อเล่น), `DELETE /favorites/{id}`, `GET /bicycles` | `eakapol/favorites.py`, `routers/bicycle.py` | `favorite`, `bicycle` |
| `/lost-items` | `modules/akeapon/pages/LostItemsPage.jsx` | `GET /lost-items` (ทั้งระบบ), `POST /lost-items`, `PUT /lost-items/{id}`, `DELETE /lost-items/{id}`, `GET /bicycles` | `eakapol/lost_items.py`, `routers/bicycle.py` | `lost_item`, `bicycle` |
| `/profile` | `modules/auth/ProfilePage.jsx` | ดูหัวข้อ 3 (แยกตามแท็บ) | หลาย router | หลายตาราง |
| `/admin` | `modules/auth/AdminDashboard.jsx` | `GET /admin/users`, `PATCH /admin/users/{id}/role` | `routers/user.py` | `accounts_unifieduser` |
| `/admin/bikes` | `modules/auth/BikesAdminPage.jsx` | `GET/POST/PUT /bicycles`, `PATCH /bicycles/{id}/status`, `DELETE /bicycles/{id}` | `routers/bicycle.py` | `bicycle` |

---

## 3. รายละเอียดรายหน้า/รายส่วน

### 3.1 ข้อมูลระดับแอป (ใช้ทุกหน้า)

| ส่วน UI | ข้อมูล | API | ตาราง |
|---|---|---|---|
| ชื่อผู้ใช้บน header/sidebar (`Layout.jsx`) | `currentUser` | `GET /auth/me` | `accounts_unifieduser` |
| `getUserName()` / dropdown ผู้ใช้ | รายชื่อผู้ใช้ทั้งหมด (โหลดครั้งเดียวใน context) | `GET /users` | `accounts_unifieduser` |
| กระดิ่ง 🔔 dropdown (`Layout.jsx`) | `notifications`, `unreadCount` | `GET /notifications/user/{id}` | `notifications` |
| ปุ่มออกจากระบบ | — | `POST /auth/logout` | session |

### 3.2 `/bookings` — BookingsPage.jsx

| ส่วน UI ในหน้า | ข้อมูลมาจาก | API | ตาราง |
|---|---|---|---|
| การ์ดจักรยานเลือกจอง | `bikes` | `GET /bicycles` | `bicycle` |
| "การจองของฉัน" (+ มุมมองแอดมิน `scope=all`) | `myBookings` | `GET /bookings?user_id=` หรือ `GET /bookings` | `reservation_booking` |
| ปุ่ม รับรถ/คืนรถ/ยกเลิก/ยืนยัน | action | `POST /bookings/{id}/{borrow\|return\|cancel\|confirm}` | `reservation_booking` |
| ปุ่ม เลื่อนเวลา | edit | `PUT /bookings/{id}` | `reservation_booking` |
| ล้างประวัติ | — | `DELETE /bookings/history?user_id=` | `reservation_booking` |
| ปุ่ม ♥ (FavoriteButton) | `favorites.js` | `POST /favorites` / `DELETE /favorites/{id}` | `favorite` |
| ปุ่ม "แจ้งปัญหา" (modal) | ฟอร์ม | `POST /tickets` | `support_ticket` |
| ปุ่ม "แจ้งของหาย" (LostItemModal) | ฟอร์ม → `handleLostSaved` | `POST /lost-items` | `lost_item` |
| "การแจ้งของหายของฉัน" (LostItemHistory) | `lostItems` — ชุดเดียวกับแท็บโปรไฟล์ + ลิงก์ไป `/profile?tab=lost` | `GET /lost-items/user/{id}` | `lost_item` |
| popup ให้คะแนนหลังคืนรถ (Stars) | ฟอร์ม | `POST /reviews` (+ `POST /upload` ถ้ามีรูป) | `reviews` |

### 3.3 `/profile` — ProfilePage.jsx (แยกตามแท็บ `?tab=`)

| แท็บ | ส่วน UI | API | ตาราง |
|---|---|---|---|
| `info` / `edit` | ข้อมูลฉัน, แก้ไขชื่อ | `GET /auth/me` (จาก context), `PATCH /auth/me` | `accounts_unifieduser` |
| `tickets` | การ์ดแจ้งปัญหาของฉัน + ฟอร์มใหม่ | `GET /tickets?user_id=`, `POST /tickets`, `POST /upload` (รูป) | `support_ticket` |
| `favorites` | การ์ดรายการโปรด + ตั้งชื่อเล่น/ลบ | `GET /favorites/user/{id}`, `PUT/DELETE /favorites/{id}` | `favorite` |
| `maintenance` | การ์ดแจ้งซ่อมของฉัน + ฟอร์ม | `GET /maintenance-reports/user/{id}`, `POST /maintenance-reports`, `POST /upload` | `maintenance_reports` |
| `reviews` | การ์ดรีวิว (หัว: ⭐ ดาว · คำโปรย / ในส่วนเหตุผล: **คอมเมนต์ comment เด่น** + muted: คำโปรย · วันที่ / รหัสจักรยานท้ายการ์ด) | `GET /reviews/user/{id}`, `POST /reviews` | `reviews` |
| `scores` | การ์ดแต้ม/บทลงโทษ | `GET /penalties/user/{id}` | `penalty_strike` |
| `lost` 🎒 | ของหายของตัวเอง (ฟอร์มแจ้ง + เจอแล้ว/ลบ) | `GET /lost-items/user/{id}`, `POST/PUT/DELETE /lost-items/{id}` | `lost_item` |
| ทุกแท็บ | ชื่อรถในการ์ด | `GET /bicycles` | `bicycle` |

### 3.4 `/lost-items` — LostItemsPage.jsx (ของทั้งระบบ)

| ส่วน UI | ข้อมูล | API | ตาราง |
|---|---|---|---|
| รายการของหายทุกคน (แสดง "ผู้แจ้ง") | `items` | `GET /lost-items` | `lost_item` |
| ฟอร์มแจ้งของหาย | ฟอร์ม | `POST /lost-items` | `lost_item` |
| ปุ่ม เจอแล้ว / ลบ (เฉพาะเจ้าของหรือแอดมิน) | — | `PUT /lost-items/{id}` / `DELETE /lost-items/{id}` | `lost_item` |
| ชื่อรถ/รหัส | `bikes` | `GET /bicycles` | `bicycle` |

### 3.5 หน้าอื่น ๆ

| หน้า | ส่วน UI | API | ตาราง |
|---|---|---|---|
| `/reviews` | การ์ดรีวิวต่อคัน + สรุปคะแนน + ฟอร์มเขียนรีวิว | `GET /reviews/bicycle/{id}`, `/summary`, `POST /reviews`, `DELETE /reviews/{id}` | `reviews` |
| `/scores` | การ์ดคะแนน/ประวัติลงโทษ | `GET /penalties/user/{id}` | `penalty_strike` |
| `/group-rides` | การ์ดกลุ่มปั่น + เข้าร่วม/ออก/สร้าง/แก้/ยกเลิก | `/group-rides*` | `group_ride`, `group_ride_member` |
| `/notifications` | รายการแจ้งเตือน + อ่านแล้ว/ล้าง | `/notifications*` | `notifications` |
| `/admin` | ตารางผู้ใช้ + เปลี่ยนบทบาท | `GET /admin/users`, `PATCH /admin/users/{id}/role` | `accounts_unifieduser` |
| `/admin/bikes` | ตารางจักรยาน CRUD + เปิด/ปิดใช้งาน | `/bicycles*` | `bicycle` |


---

## 4. ตารางในฐานข้อมูลทั้งหมด (SQLAlchemy Models)

| ตาราง | Model (ไฟล์) | คอลัมน์สำคัญ | ใช้ที่หน้า |
|---|---|---|---|
| `accounts_unifieduser` | `models/unified_user.py` | `id, username, first_name, last_name, email, is_staff, points, full_name (property)` | ทุกหน้า (context), `/admin` |
| `bicycle` | `models/bicycle.py` | `id, code, type, model, station, distance, tint, battery, is_active` | `/bookings`, `/favorites`, `/reviews`, `/lost-items`, `/maintenance`, `/admin/bikes` |
| `reservation_booking` | `models/booking.py` | `id, user_id, bicycle_id, booking_type, start_time, end_time, status (pending→confirmed→in_progress→completed/cancelled/no_show), pickup/return_location, note, pickup_reminded_at, overdue_notified_at` | `/bookings` |
| `support_ticket` | `models/booking.py` | `id, user_id, assigned_to, subject, description, category, priority, status, resolution_notes, resolved_at` | `/support`, แท็บ 🎫 โปรไฟล์, ปุ่มแจ้งปัญหาในการจอง |
| `group_ride` | `models/group_ride.py` | `id, created_by, name, destination, meetup_location/time, max_members, current_members, status (open/full/cancelled/completed)` | `/group-rides` |
| `group_ride_member` | `models/group_ride.py` | `group_ride_id, user_id, role (leader/member), joined_at, left_at` | `/group-rides` |
| `notifications` | `models/nathida.py` | `id, user_id, title, message, is_read, created_at` | กระดิ่ง header, `/notifications` |
| `maintenance_reports` | `models/nathida.py` | `id, bicycle_id, reported_by, issue_type, description, status, images (JSONB), reported_at, resolved_at` | `/maintenance`, แท็บ 🔧 โปรไฟล์ |
| `reviews` | `models/nathida.py` | `id, user_id, bicycle_id, reviewer_name, rating (float 1–5), comment, created_at` | `/reviews`, แท็บ ⭐ โปรไฟล์, popup ให้คะแนนหลังคืนรถ |
| `favorite` | `models/eakapol.py` | `id, user_id, target_type (bicycle/station), bicycle_id, station_name, nickname, created_at` | `/favorites`, แท็บ ♥ โปรไฟล์, ปุ่ม ♥ ในการ์ดจอง |
| `penalty_strike` | `models/eakapol.py` | `id, user_id, reason (late_return/damaged/lost/other/good_behavior/no_violation_week), penalty_points, action, suspension_days, completed` | `/scores`, แท็บ 🏆 โปรไฟล์ |
| `lost_item` | `models/eakapol.py` | `id, user_id, bicycle_id, item_name, location, image_url, description, status (lost/found), found_at, created_at` | `/lost-items`, แท็บ 🎒 โปรไฟล์, "การแจ้งของหายของฉัน" ในการจอง |

---

## 5. ฝั่ง Backend ที่ทำงานเอง (ไม่มีหน้าเรียกโดยตรง)

| ระบบ | ไฟล์ | ทำอะไร | กระทบตาราง |
|---|---|---|---|
| แจ้งเตือนก่อนรับรถ/คืนรถ (FR3.6) | `modules/nathida/reminders.py` | วนตรวจการจองที่ใกล้ถึงเวลา → สร้าง notification (กันซ้ำด้วย `pickup_reminded_at` / `overdue_notified_at`) | `reservation_booking`, `notifications` |
| Seed ข้อมูลตั้งต้น | `app/seed/seed_bookings.py`, `seed_bicycles.py` | เติมจักรยาน/การจอง test | `bicycle`, `reservation_booking` |
| Static รูป | `routers/uploads.py` | `POST /api/upload` เก็บไฟล์ → path `/api/uploads/...` | ไฟล์บนดิสก์ (ไม่ใช่ตาราง) |
| Auth Google OAuth | `modules/auth/router.py` | `GET /auth/google/login` → `/callback` → สร้าง/หา user → session cookie | `accounts_unifieduser` |

---

## 6. หมายเหตุ

- **ฝั่ง UI ไม่มี mock เหลือแล้ว** — ของหาย/รายการโปรด/รีวิว/ซ่อม เชื่อม backend หมด (ไฟล์เก่า `modules/akeapon/lostItems.js` ไม่มีที่ใช้แล้ว ลบได้)
- **หน้า Home** (`pages/HomePage.jsx`) เป็น static config ล้วน — ไม่ยิง API
- **เส้นทาง Sidebar**: `components/Layout.jsx` — เมนูหลัก (`navItems` รวม `/lost-items`), เมนูแอดมิน (`adminNavItems`), เมนูโปรไฟล์ (`profileNavItems` ผูก `?tab=`)
- **โลโก้ header** (`⌁ BikeShare`) → `Link to="/"` กลับหน้า Home
- เปลี่ยนเส้นทาง API = แก้ `backend/app/main.py` (include_router) + router นั้น ๆ แล้ว restart uvicorn
- **เอกสารแยกเฉพาะบุคคล**: `datamapping-chaianan.md` (ชัยอนันต์ — จอง/ปั่นกลุ่ม/แจ้งปัญหา)

