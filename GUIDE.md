# คู่มือระบบจัดการการคืนจักรยาน (ฉบับสั้น)

> ระบบนี้ = เว็บสำหรับจัดการคืนจักรยาน มี 3 ฟีเจอร์: บันทึกการคืน, หลักฐานความเสียหาย, บทลงโทษ

---

## โครงสร้าง

```
D:\na\
├── backend\           ← หลังบ้าน (Python/FastAPI)
│   ├── main.py        ← จุดเริ่มต้นของ backend
│   ├── database.py    ← ต่อกับ PostgreSQL
│   ├── models.py      ← นิยาม 3 ตาราง (ReturnRecord, DamageEvidence, PenaltyStrike)
│   ├── schemas.py     ← รูปแบบข้อมูลเข้า-ออก API
│   ├── routers\       ← CRUD แยกตามตาราง
│   │   ├── returns.py, damages.py, penalties.py
│   └── uploads\       ← เก็บรูปภาพความเสียหาย
│
├── frontend\          ← หน้าบ้าน (React)
│   └── src\
│       ├── main.jsx   ← จุดเริ่มต้น frontend
│       ├── App.jsx    ← Tab navigation (3 tabs)
│       ├── api/index.js   ← เรียก API
│       ├── components\
│       │   ├── ReturnsManager.jsx   ← หน้าจัดการบันทึกการคืน
│       │   ├── DamagesManager.jsx   ← หน้าจัดการความเสียหาย
│       │   └── PenaltiesManager.jsx ← หน้าจัดการบทลงโทษ
│       └── index.css  ← ตกแต่งหน้าตา
│
└── GUIDE.md           ← ไฟล์นี้
```

---

## แต่ละไฟล์คืออะไร?

### backend/

| ไฟล์ | หน้าที่ |
|------|---------|
| `main.py` | รวมทุกอย่าง: สร้าง app, ต่อ CORS, ต่อ router, mount uploads |
| `database.py` | บอกให้ใช้ PostgreSQL, มีฟังก์ชัน `get_db()` ให้ router ใช้ |
| `models.py` | กำหนดว่าตารางมี column อะไร, FK, ความสัมพันธ์ |
| `schemas.py` | กำหนดว่าเวลา POST/PUT ต้องส่งอะไร, GET ได้อะไรกลับ |
| `routers/returns.py` | `GET/POST/PUT/DELETE /api/returns/...` |
| `routers/damages.py` | เหมือน returns + อัปโหลดรูป |
| `routers/penalties.py` | เหมือน returns + ค้นหาตาม user |

### frontend/src/

| ไฟล์ | หน้าที่ |
|------|---------|
| `main.jsx` | เอา `<App />` ไปใส่ใน `index.html` |
| `App.jsx` | มี 3 tabs, กด tab ไหนก็แสดง component นั้น |
| `api/index.js` | รวมฟังก์ชันเรียก API: `.list()`, `.create()`, `.update()`, `.delete()` |
| `ReturnsManager.jsx` | ฟอร์ม + ตาราง CRUD บันทึกการคืน |
| `DamagesManager.jsx` | ฟอร์ม + ตาราง + เลือก return record + อัปโหลดรูป |
| `PenaltiesManager.jsx` | ฟอร์ม + ตาราง + ค้นหาตาม user |
| `index.css` | สี ปุ่ม ตาราง layout |

---

## 3 ตาราง กับ API

### 1. return_records — บันทึกการคืน

| คอลัมน์ | ประเภท | คำอธิบาย |
|---------|--------|----------|
| id | int PK | เลข自動 |
| bike_id | text | รหัสจักรยาน |
| user_id | text | รหัสผู้ใช้ |
| return_time | datetime | เวลาคืน |
| station | text | สถานี |
| status | enum | on_time / late / damaged |
| notes | text | หมายเหตุ |

**API:**
- `GET /api/returns/` — ดูทั้งหมด
- `GET /api/returns/{id}` — ดูรายการเดียว
- `POST /api/returns/` — เพิ่ม (JSON)
- `PUT /api/returns/{id}` — แก้ไข (JSON)
- `DELETE /api/returns/{id}` — ลบ

### 2. damage_evidence — ความเสียหาย

| คอลัมน์ | ประเภท | คำอธิบาย |
|---------|--------|----------|
| id | int PK | |
| return_id | int FK→return_records | เชื่อมโยงการคืน |
| description | text | รายละเอียดเสียหาย |
| image_paths | text | ชื่อไฟล์รูป คั่น `,` |
| severity | text | minor / moderate / severe |

**API:**
- `GET /api/damages/`
- `POST /api/damages/` — เพิ่ม (FormData: return_id + description + รูป)
- `PUT /api/damages/{id}` — แก้ไข
- `DELETE /api/damages/{id}` — ลบ (รวมลบรูป)

### 3. penalty_strikes — บทลงโทษ

| คอลัมน์ | ประเภท | คำอธิบาย |
|---------|--------|----------|
| id | int PK | |
| user_id | text | รหัสผู้ใช้ |
| return_id | int FK→return_records (SET NULL) | |
| points | int | คะแนนโทษ |
| reason | text | เหตุผล |
| status | enum | active / appealed / removed |

**API:**
- `GET /api/penalties/` — ดูทั้งหมด
- `GET /api/penalties/user/{user_id}` — ค้นหาตาม user
- `POST /api/penalties/` — เพิ่ม (JSON)
- `PUT /api/penalties/{id}` — แก้ไข
- `DELETE /api/penalties/{id}` — ลบ

---

## Flow เวลา user กด "เพิ่ม"

```
User กดปุ่ม → ReturnsManager.handleSubmit()
           → api/index.js ส่ง fetch(POST /api/returns/)
           → Vite proxy ส่งต่อ localhost:8002
           → routers/returns.py สร้าง Record + db.commit()
           → ส่ง JSON กลับ → โหลดตารางใหม่
```

---

## อยากแก้อะไร?

| อยาก | ทำยังไง |
|------|---------|
| เพิ่มคอลัมน์ในตาราง | แก้ `models.py` + `schemas.py` + component `.jsx` |
| เพิ่ม Tab ใหม่ | สร้าง component → แก้ `App.jsx` (เพิ่มใน TABS array) |
| เพิ่ม API endpoint | เพิ่มฟังก์ชันใน `routers/*.py` |
| เปลี่ยนสี/ฟอนต์ | แก้ `index.css` |

---

## วิธีรัน

```bash
# Terminal 1
cd backend
python -m uvicorn main:app --reload --port 8002

# Terminal 2
cd frontend
npm run dev
```

เปิด `http://localhost:5173`
