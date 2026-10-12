# BikeShare — ระบบจัดการจักรยาน + ประกาศข่าวสาร

ระบบเว็บแบบโมโนลิธบน **Django** รวมหลายระบบไว้ด้วยกัน:
- **จักรยาน & ซ่อมบำรุง** (แอดมิน/เจ้าหน้าที่ จัดการรถ ค้นหา แก้ไขสถานะ และรายงานซ่อม)
- **ประกาศข่าวสาร** (เผยแพร่/จัดการหมวดหมู่ ตามสิทธิ์ผู้ใช้)
- **บัญชี & เจ้าหน้าที่** (สมัครสมาชิก ล็อกอิน ขอสิทธิ์เจ้าหน้าที่ แอดมินอนุมัติ)

UI ทั้งหมดทำด้วยเทมเพลต Django + CSS ชุด `bs-*` (`core/static/css/bikeshare.css`) ไม่มี frontend แยก

---

## 1) ติดตั้งและรัน

ต้องมี Python 3.12+ และ virtualenv (`.venv`) ในโฟลเดอร์โปรเจกต์

```powershell
# 1) สร้าง/เปิด virtualenv (ถ้ายังไม่มี)
py -3 -m venv .venv
.venv\Scripts\Activate.ps1

# 2) ติดตั้งไลบรารี
.venv\Scripts\pip.exe install -r requirements.txt

# 3) สร้างตารางฐานข้อมูล (SQLite)
.venv\Scripts\python.exe manage.py migrate

# 4) (แนะนำ) สร้างข้อมูลตัวอย่างเพื่อให้เห็นข้อมูลจริง
.venv\Scripts\python.exe seed_mock.py

# 5) รันเซิร์ฟเวอร์
.venv\Scripts\python.exe manage.py runserver
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:8000/

---

## 2) บัญชีตัวอย่าง (จาก `seed_mock.py`)

> ล็อกอินด้วย **username** (ไม่รองรับอีเมล)

| Username | รหัสผ่าน | สิทธิ์ (role) | หมายเหตุ |
|---|---|---|---|
| `admin` | `admin1234` | ADMIN | แอดมินสูงสุด เห็นทุกเมนู |
| `manager1` | `manager1234` | MANAGER | เจ้าหน้าที่ อนุมัติแล้ว |
| `student1` | `student1234` | ผู้ใช้ทั่วไป (BASIC) | นักศึกษา |
| `student_pending` | `student1234` | ผู้ใช้ทั่วไป | ยื่นขอสิทธิ์เจ้าหน้าที่ รออนุมัติ |

บัญชีแอดมินเริ่มต้น (ถ้าไม่รัน seed) คือ `admin` / `admin1234`

---

## 3) ฟีเจอร์ตามสิทธิ์ผู้ใช้

| หน้า | URL | ใครเข้าได้ |
|---|---|---|
| หน้าแรก (hub) | `/` | ทุกคน |
| จักรยานทั้งหมด | `/bicycles/` | ทุกคนที่ล็อกอิน |
| เพิ่มจักรยาน | `/bicycles/add/` | ADMIN/MANAGER |
| Dashboard สถิติ | `/dashboard/` | ADMIN/MANAGER |
| รายการแจ้งซ่อม | `/maintenance/` | ADMIN/MANAGER |
| รายงานซ่อมใหม่ | `/maintenance/add/` | ADMIN/MANAGER |
| จัดการประกาศ | `/announcements/manage/` | ADMIN/MANAGER |
| จัดการหมวดหมู่ | `/announcements/categories/` | ADMIN |
| จัดการเจ้าหน้าที่ | `/staff/` | ADMIN |
| ขอสิทธิ์เจ้าหน้าที่ | `/staff/request-access/` | ผู้ใช้ที่ล็อกอิน |

สิทธิ์ถูกกำหนดจาก `StaffProfile` (ดู `accounts/models.py` → `UnifiedUser.role`)

---

## 4) โครงสร้างโปรเจกต์

```
config/            การตั้งค่าโปรเจกต์ + URLs หลัก
accounts/          บัญชีผู้ใช้ + สมัคร/ล็อกอิน + role redirect
core/              จักรยาน + ซ่อมบำรุง + dashboard + CSS + หน้าแรก
announcements/     ประกาศข่าวสาร + หมวดหมู่
staff/             โปรไฟล์เจ้าหน้าที่ + ขอสิทธิ์/อนุมัติ
audit/             บันทึก audit log
templates/         เทมเพลตหลัก (base.html, components, หน้า core)
core/templates/    หน้าแรก (home.html)
seed_mock.py       สคริปต์สร้างข้อมูลตัวอย่าง
requirements.txt   ไลบรารีที่ต้องติดตั้ง
```

เทมเพลตย่อยที่ใช้ร่วมกันอยู่ใน `templates/core/`:
`_field.html` `_toolbar.html` `_pager.html` `_icons.html` `_maintenance_actions.html`

---

## 5) (ทางเลือก) ล็อกอินผ่าน Google

ระบบรองรับ Google OAuth 2.0 แต่จะแสดงปุ่มก็ต่อเมื่อใส่คีย์ในไฟล์ `.env`
ดูขั้นตอนทั้งหมดใน [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

```powershell
Copy-Item .env.example .env   # แล้วแปะ Client ID / Secret
```

> ไฟล์ `.env` ถูกลง `.gitignore` อยู่แล้ว ห้าม commit คีย์จริงขึ้น Git

---

## 6) หมายเหตุสำคัญ

- ล็อกอินด้วย **username** เท่านั้น (ถอยจากระบบล็อกอินด้วยอีเมลแล้ว)
- ฐานข้อมูลตัวอย่างคือ `db.sqlite3` (ถูกลง `.gitignore`)
- ข้อมูล log ของเซิร์ฟเวอร์ (`runserver.*`) ไม่น่า commit ถูกลง `.gitignore` แล้ว
