# BikeA — Online Bicycle Booking

ระบบจอง/คืนจักรยาน + ปั่นกลุ่ม + แจ้งปัญหา (FastAPI + React)

## โครงสร้าง

```
backend/    FastAPI (Python 3.14, uv)
frontend/   React 19 + Vite
docs/       Database schema / ER diagram
```

## Docker

`docker-compose.yml` มี **service เดียวคือ `db` (PostgreSQL 16)** เท่านั้น
backend และ frontend ต้องรันบนเครื่องตรง ๆ (ดูด้านล่าง)

```bash
docker compose up -d db      # ยกฐานข้อมูล (port 5434)
docker compose ps            # ดูสถานะ
docker compose down          # ปิด (เก็บข้อมูลไว้)
docker compose down -v       # ปิด + ลบ volume ข้อมูลทิ้ง
```

## Backend

```bash
cd backend
uv sync
copy .env.example .env       # Windows (macOS/Linux: cp .env.example .env)
uv run uvicorn app.main:app --reload --port 8002
```

- API: http://127.0.0.1:8002
- ต้องใช้ `127.0.0.1` ให้ตรงกับ `GOOGLE_REDIRECT_URI` ใน `.env` เพราะ OAuth cookie ผูกกับ host
  (`localhost` กับ `127.0.0.1` คือคนละ host)
- ตารางถูกสร้างและ seed ข้อมูลตัวอย่างอัตโนมัติตอน startup

ตรวจสอบ OAuth state flow:

```bash
uv run python _verify_oauth_flow.py
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://127.0.0.1:5173
- `frontend/.env` มี `VITE_API_URL=http://127.0.0.1:8002` (ต้องตรงกับ `GOOGLE_REDIRECT_URI`)

```bash
npm run lint     # eslint
npm run build    # production build -> dist/
```

