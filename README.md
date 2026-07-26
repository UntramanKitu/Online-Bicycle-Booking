# Bike Return Management System

ระบบจัดการการคืนจักรยาน — บันทึกการคืน, หลักฐานความเสียหาย, และรายการโปรด

## Tech Stack

- **Frontend:** React 19 + Vite 8
- **Backend:** Python FastAPI + SQLAlchemy
- **Database:** PostgreSQL

## วิธีรัน

### 1. Database (PostgreSQL)

ต้องมี PostgreSQL รันอยู่ที่ `localhost:5432` และสร้าง database:

```sql
CREATE DATABASE bike_returns;
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

คัดลอก `.env.example` จาก root มาเป็น `.env` และแก้ไข password:

```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/bike_returns
```

รัน:

```bash
uvicorn main:app --reload --port 8002
```

เปิด Swagger docs ที่ `http://localhost:8002/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

เปิด `http://localhost:5173`

### 4. พร้อมใช้งาน

| URL | คำอธิบาย |
|-----|---------|
| `http://localhost:5173` | Frontend UI |
| `http://localhost:8002/docs` | Swagger API Docs |
| `http://localhost:8002/uploads/<filename>` | รูปภาพความเสียหาย |

## API Endpoints

### Return Records
- `GET /api/returns/` — ดูทั้งหมด
- `GET /api/returns/{id}` — ดูรายการเดียว
- `POST /api/returns/` — เพิ่ม
- `PUT /api/returns/{id}` — แก้ไข
- `DELETE /api/returns/{id}` — ลบ

### Damage Evidence
- `GET /api/damages/` — ดูทั้งหมด
- `GET /api/damages/{id}` — ดูรายการเดียว
- `POST /api/damages/` — เพิ่ม (FormData + รูปภาพ)
- `PUT /api/damages/{id}` — แก้ไข
- `DELETE /api/damages/{id}` — ลบ

### Favorites (รายการโปรด)

ให้ผู้ใช้บันทึกจักรยานหรือสถานีที่ใช้งานประจำ โดยสามารถตั้งชื่อเล่นเพื่อให้จดจำง่าย

**ตาราง `favorites`:**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | auto increment |
| user_id | VARCHAR(50) | รหัสผู้ใช้ |
| favorite_type | VARCHAR(20) | 'bike' หรือ 'station' |
| favorite_id | VARCHAR(100) | รหัสจักรยาน หรือชื่อสถานี |
| nickname | VARCHAR(100) | ชื่อเล่น เช่น "คันโปรดเบอร์ 05" |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**ตัวอย่างการใช้งาน:**
- เพิ่มจักรยานที่ใช้ประจำเข้า Favorite → ดูสถานะได้ทันที ไม่ต้องค้นหาใหม่
- เพิ่มสถานีที่ใช้บ่อย → ตั้งชื่อเล่นว่า "สถานีหน้าหอ" จำง่าย
- ค้นหารายการโปรดตามรหัสผู้ใช้

**Endpoints:**
- `GET /api/favorites/` — ดูรายการโปรดทั้งหมด
- `GET /api/favorites/{id}` — ดูรายการเดียว
- `GET /api/favorites/user/{user_id}` — ค้นหารายการโปรดตามผู้ใช้
- `POST /api/favorites/` — เพิ่มรายการโปรด (JSON: user_id, favorite_type, favorite_id, nickname)
- `PUT /api/favorites/{id}` — แก้ไขชื่อเล่น (JSON: nickname)
- `DELETE /api/favorites/{id}` — ลบรายการโปรด
