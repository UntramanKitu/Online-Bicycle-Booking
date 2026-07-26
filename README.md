# Bike Return Management System

ระบบจัดการการคืนจักรยาน — บันทึกการคืน, หลักฐานความเสียหาย, และบทลงโทษ

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

### Penalty Strikes
- `GET /api/penalties/` — ดูทั้งหมด
- `GET /api/penalties/{id}` — ดูรายการเดียว
- `GET /api/penalties/user/{user_id}` — ค้นหาตาม user
- `POST /api/penalties/` — เพิ่ม
- `PUT /api/penalties/{id}` — แก้ไข
- `DELETE /api/penalties/{id}` — ลบ
