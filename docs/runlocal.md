# รัน localhost ที่เครื่องตัวเอง (แต่ละคนรันของตัวเอง)

> `127.0.0.1` = เครื่องตัวเองเท่านั้น ห้ามก็อป URL `127.0.0.1` ส่งให้กัน
> `502` ที่ `/api/...` แปลว่า frontend รันอยู่ แต่ backend `:8002` ไม่ได้รัน (proxy ต่อไม่ติด)

## 1. ของที่ต้องมี

- Node 20+
- Python + uv
- Docker (ใช้ยก DB อย่างเดียว)

## 2. Clone + ยก DB

```bash
git clone <repo-url>
cd BikeA
docker compose up -d db
```

DB รันที่ `127.0.0.1:5434` (user/pass/db = `bikea`)

## 3. Backend `.env`

```bash
cd backend
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

เปิด `backend/.env` ใส่ค่าจริง 3 ตัวนี้ (ขอหลังไมค์ ห้าม commit):

```ini
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...
```

ที่เหลือคง `127.0.0.1` ไว้เหมือนเดิม:

```ini
GOOGLE_REDIRECT_URI=http://127.0.0.1:8002/api/auth/google/callback
FRONTEND_URL=http://127.0.0.1:5173
DB_HOST=127.0.0.1
DB_PORT=5434
DB_NAME=bikea
DB_USER=bikea
DB_PASSWORD=bikea
AUTH_USER_PROVISIONING=true
```

## 4. Frontend `.env`

```bash
cd ../frontend
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

ข้างในต้องเป็น:

```ini
VITE_API_URL=http://127.0.0.1:8002
```

## 5. รัน 2 ตัว

```bash
# terminal 1 - backend
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8002

# terminal 2 - frontend
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

หรือดับเบิลคลิก `start-dev.bat` (ทำเหมือนกัน)

## 6. เปิดที่เครื่องตัวเอง

```
http://127.0.0.1:5173/login
```

## 7. เช็คตอนพัง

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `502` ที่ `:5173/api/...` | backend `:8002` ไม่ได้รัน / crash / ผิด port — เปิด `http://127.0.0.1:8002/docs` ถ้าไม่ติดคือ backend ยังไม่ติด |
| `503 Google OAuth ยังไม่ได้ตั้งค่า` | `backend/.env` ไม่มี `GOOGLE_CLIENT_ID/SECRET` |
| วนลูป / `oauth_failed` | เปิด `localhost` ปนกับ `127.0.0.1` — cookie คนละ host ให้ใช้ `127.0.0.1` ทั้งหมด |
| `user_not_registered` | ปกติ: Google ผ่านแล้วแต่ email นี้ยังไม่มีใน DB เช็ค `AUTH_USER_PROVISIONING=true` |
| backend รันแล้วดับเลย | DB ยังไม่ขึ้น — `docker compose up -d db` ก่อน |
