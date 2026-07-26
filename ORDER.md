# เริ่มเขียนจากไหนไปไหน แต่ละไฟล์เชื่อมกันยังไง

> แผนที่เดินทางสำหรับคนอยากเข้าใจว่าทำไมถึงเรียงไฟล์แบบนี้

---

## หลักการ: เขียนไฟล์ที่ "ไม่มีคนอื่น依赖" ก่อน

```
backend/                          frontend/
─────────────────────────────────────────────────────
① database.py        (พึ่งตัวเอง)    
② models.py          (พึ่ง database.py)
③ schemas.py         (พึ่งตัวเอง)
④ routers/returns.py (พึ่ง database + models + schemas)
⑤ main.py            (พึ่ง router + database)
                                   ⑥ api/index.js  (พึ่งตัวเอง)
                                   ⑦ components/   (พึ่ง api/index.js)
                                   ⑧ App.jsx       (พึ่ง components)
                                   ⑨ main.jsx      (พึ่ง App.jsx)
                                   ⑩ index.css     (พึ่งตัวเอง)
```

---

## แผนภาพการเชื่อมต่อ

```
backend:

database.py ◄────────────── models.py (import Base)
    ▲                            │
    │                            │
    ├──── routers/returns.py ────┤ (import get_db + ReturnRecord + schemas)
    ├──── routers/damages.py ────┤
    └──── routers/penalties.py ──┘
                │
                └──── main.py ─── import router 3 ตัว + database → สร้างตาราง

frontend:

api/index.js ◄──── components/ReturnsManager.jsx (import returnsApi)
              ◄──── components/DamagesManager.jsx (import damagesApi)
              ◄──── components/PenaltiesManager.jsx (import penaltiesApi)
                                │
                                └──── App.jsx ──── import component 3 ตัว
                                                    │
                                                    └──── main.jsx ──── import App
```

---

## อธิบายทีละไฟล์ — เขียนก่อน-หลัง

### ① `database.py` — เขียนก่อนสุด

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine("sqlite:///./bike_returns.db")
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):     ← ตัวแม่ของ models ทั้งหมด
    pass

def get_db():                    ← router เรียกใช้เวลาจะอ่าน/เขียน DB
    db = SessionLocal()
    yield db
    db.close()
```

**เชื่อมไปหา:** models.py (import Base), routers/*.py (import get_db)

---

### ② `models.py` — ต้องมี database.py ก่อน

```python
from database import Base       ← ขอยืม Base มาใช้

class ReturnRecord(Base):       ← Base ทำให้ ReturnRecord กลายเป็นตารางใน DB
    __tablename__ = "return_records"
    id = Column(...)
    bike_id = Column(...)

class DamageEvidence(Base):
    __tablename__ = "damage_evidence"
    return_id = Column(ForeignKey("return_records.id"))  ← เชื่อมกับ ReturnRecord

class PenaltyStrike(Base):
    __tablename__ = "penalty_strikes"
    return_id = Column(ForeignKey("return_records.id", ondelete="SET NULL"))
```

**เชื่อมไปหา:** routers/*.py (import ReturnRecord, DamageEvidence, PenaltyStrike)

---

### ③ `schemas.py` — พึ่งตัวเอง ไม่ต้อง import ไฟล์โปรเจค

```python
from pydantic import BaseModel

class ReturnRecordCreate(BaseModel):    ← บอกว่าเวลา POST ต้องส่งอะไรบ้าง
    bike_id: str
    user_id: str
    return_time: datetime
    ...

class ReturnRecordUpdate(BaseModel):   ← บอกว่าเวลา PUT ส่งอะไรก็ได้ (Optional)
    bike_id: Optional[str] = None
    ...

class ReturnRecordResponse(ReturnRecordCreate):  ← บอกว่า GET จะได้อะไรกลับ
    id: int
    created_at: datetime
```

**เชื่อมไปหา:** routers/*.py (ใช้เป็น type hint, response_model)

---

### ④ `routers/returns.py`, `damages.py`, `penalties.py`

```python
from database import get_db             ← เอาไว้เปิด session
from models import ReturnRecord         ← ตัวแทนตาราง
from schemas import ReturnRecordCreate, ReturnRecordUpdate, ReturnRecordResponse  ← รูปแบบข้อมูล

router = APIRouter(prefix="/api/returns")

@router.get("/")
def list(db: Session = Depends(get_db)):       ← Depends = ขอ get_db มาใช้
    return db.query(ReturnRecord).all()         ← SELECT * FROM return_records

@router.post("/")
def create(data: ReturnRecordCreate, db = Depends(get_db)):
    record = ReturnRecord(**data.model_dump())  ← แปลง JSON → object
    db.add(record)
    db.commit()
    return record
```

**เชื่อมไปหา:** main.py (app.include_router(returns.router))

---

### ⑤ `main.py` — รวมทุกอย่าง

```python
from database import engine, Base
from routers import returns, damages, penalties

Base.metadata.create_all(bind=engine)   ← อ่าน models → สร้างตารางใน DB

app = FastAPI()
app.include_router(returns.router)      ← ต่อ router 3 ตัว
app.include_router(damages.router)
app.include_router(penalties.router)
```

**จบ backend** — รัน `python -m uvicorn main:app --reload` ก็ใช้ได้

---

### ⑥ `api/index.js` — frontend ไฟล์แรก

```javascript
const API = '/api'

async function request(url, options) {
  const res = await fetch(url, { ... })
  return res.json()
}

export const returnsApi = {           ← export ไว้ให้ component ใช้
  list: () => request(`${API}/returns/`),
  create: (data) => request(`${API}/returns/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => ...,
  delete: (id) => ...,
}
```

**เชื่อมไปหา:** components/*Manager.jsx (import returnsApi, damagesApi, penaltiesApi)

---

### ⑦ `components/*Manager.jsx` — หน้าจริง ๆ

```jsx
import { returnsApi } from '../api'

function ReturnsManager() {
  const [records, setRecords] = useState([])

  useEffect(() => {                    ← เปิดหน้ามา → โหลดข้อมูล
    returnsApi.list().then(setRecords)
  }, [])

  async function handleSubmit(e) {     ← กดปุ่ม → ส่ง API
    await returnsApi.create(form)
    load()  // โหลดใหม่
  }

  return (
    <form onSubmit={handleSubmit}>...</form>
    <table>...</table>
  )
}
```

**เชื่อมไปหา:** App.jsx (import ReturnsManager)

---

### ⑧ `App.jsx` — รวม component ทั้งหมด

```jsx
import ReturnsManager from './components/ReturnsManager'
import DamagesManager from './components/DamagesManager'
import PenaltiesManager from './components/PenaltiesManager'

const TABS = [
  { key: 'returns', label: 'บันทึกการคืน' },
  { key: 'damages', label: 'ความเสียหาย' },
  { key: 'penalties', label: 'บทลงโทษ' },
]

function App() {
  const [tab, setTab] = useState('returns')
  return (
    <>
      <nav>{TABS.map(t => <button onClick={() => setTab(t.key)}>{t.label}</button>)}</nav>
      {tab === 'returns' && <ReturnsManager />}
      {tab === 'damages' && <DamagesManager />}
      {tab === 'penalties' && <PenaltiesManager />}
    </>
  )
}
```

**เชื่อมไปหา:** main.jsx (import App)

---

### ⑨ `main.jsx` — ไฟล์สุดท้าย

```jsx
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(<App />)
```

---

### ⑩ `index.css` — ไม่เชื่อมกับใคร

แค่ import ใน `main.jsx` บรรทัด: `import './index.css'`

---

## สรุปสั้น ๆ (จำง่าย)

```
backend:
  database.py  ← รองรับทุกคน
  models.py    ← ใช้ database.py
  schemas.py   ← ใช้ตัวมันเอง
  routers/     ← ใช้ database + models + schemas
  main.py      ← ใช้ routers + database

frontend:
  api/index.js ← รองรับ component
  components/  ← ใช้ api/index.js
  App.jsx      ← ใช้ components
  main.jsx     ← ใช้ App.jsx
  index.css    ← ไม่พึ่งใคร
```
