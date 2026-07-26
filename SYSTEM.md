# ระบบจัดการการคืนจักรยาน (Bike Return Management System)

## สถาปัตยกรรม

```
┌───────────────────────┐       ┌──────────────────────┐
│   Frontend (React)    │──────>│   Backend (FastAPI)   │
│   localhost:5173      │proxy  │   localhost:8002      │
│                       │       │                       │
│  Vite dev server      │       │  PostgreSQL database   │
│  proxy /api -> :8002  │       │  uploads/ (images)    │
└───────────────────────┘       └──────────────────────┘
```

Frontend เรียก API ผ่าน Vite proxy (ไม่มี CORS issue)  
Backend เสิร์ฟรูปภาพที่ `/uploads/<filename>`  
Database ใช้ PostgreSQL (本地หรือ雲端)

---

## โครงสร้างไฟล์

```
backend/
├── main.py              # Entry point, CORS, mount static files
├── database.py          # SQLAlchemy engine + session (PostgreSQL)
├── models.py            # 3 ORM models
├── schemas.py           # Pydantic request/response schemas
├── routers/
│   ├── returns.py       # CRUD /api/returns/
│   ├── damages.py       # CRUD /api/damages/ + image upload
│   └── penalties.py     # CRUD /api/penalties/
├── uploads/             # stored uploaded images
└── database.py           # PostgreSQL connection string

frontend/
└── src/
    ├── api/index.js              # API client functions
    ├── components/
    │   ├── ReturnsManager.jsx    # Tab: บันทึกการคืน
    │   ├── DamagesManager.jsx    # Tab: ความเสียหาย
    │   └── PenaltiesManager.jsx  # Tab: บทลงโทษ
    ├── App.jsx                   # 3-tab navigation
    └── index.css                 # 全局 styles
```

---

## ตารางฐานข้อมูล

### 1. return_records — บันทึกการคืนจักรยาน

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | auto increment |
| bike_id | VARCHAR(50) | รหัสจักรยาน |
| user_id | VARCHAR(50) | รหัสผู้ใช้ |
| return_time | DATETIME | เวลาที่คืน |
| station | VARCHAR(100) | สถานีที่คืน |
| status | ENUM('on_time','late','damaged') | สถานะ |
| notes | TEXT | หมายเหตุ |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**Endpoints:**
- `GET /api/returns/` — list ทั้งหมด
- `GET /api/returns/{id}` — รายการเดียว
- `POST /api/returns/` — สร้าง (JSON body)
- `PUT /api/returns/{id}` — แก้ไข
- `DELETE /api/returns/{id}` — ลบ

### 2. damage_evidence — หลักฐานความเสียหาย

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| return_id | INTEGER FK → return_records.id | เชื่อมโยงการคืน |
| description | TEXT | รายละเอียดเสียหาย |
| image_paths | TEXT | ชื่อไฟล์รูป คั่นด้วย `,` |
| severity | VARCHAR(20) | 'minor','moderate','severe' |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**Endpoints:**
- `GET /api/damages/` — list
- `GET /api/damages/{id}` — รายการเดียว
- `POST /api/damages/` — สร้าง (FormData: return_id, description, severity, images[])
- `PUT /api/damages/{id}` — แก้ไข (FormData)
- `DELETE /api/damages/{id}` — ลบ + ลบไฟล์รูป

### 3. penalty_strikes — บทลงโทษ

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| user_id | VARCHAR(50) | รหัสผู้ใช้ |
| return_id | INTEGER FK → return_records.id (SET NULL) | |
| points | INTEGER | คะแนนโทษ |
| reason | TEXT | เหตุผล |
| status | ENUM('active','appealed','removed') | สถานะ |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**Endpoints:**
- `GET /api/penalties/` — list ทั้งหมด
- `GET /api/penalties/{id}` — รายการเดียว
- `GET /api/penalties/user/{user_id}` — ค้นหาตาม user
- `POST /api/penalties/` — สร้าง (JSON body)
- `PUT /api/penalties/{id}` — แก้ไข
- `DELETE /api/penalties/{id}` — ลบ

---

## วิธีรัน

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn main:app --reload --port 8002

# Terminal 2: Frontend
cd frontend
npm run dev
```

เปิด `http://localhost:5173`

---

## หมายเหตุ

- ใช้ PostgreSQL, ต้องมี PostgreSQL server กำลังรันอยู่
- รูปภาพเก็บใน `backend/uploads/` เสิร์ฟผ่าน `/uploads/<filename>`
- ใช้ `ondelete="CASCADE"` — ลบ return record แล้ว damage จะถูกลบตาม
- ใช้ `ondelete="SET NULL"` — ลบ return record แล้ว penalty strike จะเป็น null
