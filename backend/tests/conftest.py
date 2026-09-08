"""
Test fixtures ที่ทุกไฟล์ test_*.py ใช้ร่วมกัน

จุดสำคัญ: ใช้ SQLite in-memory แยกต่างหาก ไม่แตะฐานข้อมูล Supabase จริงเลย
(override get_db ของ FastAPI ด้วย session ที่ผูกกับ SQLite แทน)
"""
import os
import sys

# ให้ import "database", "models", "main" ฯลฯ (อยู่ใน backend/) ได้ ไม่ว่าจะรัน
# pytest จากที่ไหนก็ตาม
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base, get_db
from models import UnifiedUser, Bicycle
import main

# StaticPool = ทุก session ใช้ connection เดียวกันจริงๆ จำเป็นสำหรับ SQLite
# in-memory ไม่งั้นแต่ละ session จะเห็นฐานข้อมูลคนละใบ (ว่างเปล่า)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _fresh_schema():
    """สร้างตารางใหม่ก่อนทุกเทส แล้วลบทิ้งหลังจบ — แต่ละเทสไม่เห็นข้อมูลของกันและกัน"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    # ไม่ใช้ "with TestClient(...) as c" เพราะจะไปทริกเกอร์ lifespan ของ main.py
    # ซึ่งพยายามต่อฐานข้อมูลจริง (Supabase) — ไม่ต้องการแบบนั้นตอนเทส
    #
    # ทดสอบทั่วไปสมมติว่าเรียกโดยแอดมิน (สิทธิ์เต็ม) เป็นค่าเริ่มต้น — เทสเรื่องสิทธิ์
    # ผู้ใช้ทั่วไป/เจ้าของข้อมูลโดยเฉพาะ ให้ใช้ fixture "user_client" แทน
    c = TestClient(main.app)
    c.headers.update({"X-Actor-Role": "admin"})
    return c


@pytest.fixture
def user_client():
    """factory: user_client(user_id) -> TestClient ที่ "สวมบทบาท" เป็นผู้ใช้ทั่วไปคนนั้น"""
    def _make(user_id):
        c = TestClient(main.app)
        c.headers.update({"X-Actor-Role": "user", "X-Actor-User-Id": str(user_id)})
        return c
    return _make


@pytest.fixture
def anonymous_client():
    """ไม่แนบ header ระบุตัวตนเลย — พฤติกรรมเริ่มต้นต้องปลอดภัยไว้ก่อน (เหมือน role=user ไม่มี id)"""
    return TestClient(main.app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def user(db_session):
    """ผู้ใช้ทดสอบ 1 คน แต้มเต็ม 12"""
    u = UnifiedUser(username="testuser", points=12)
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def bike(db_session):
    b = Bicycle(bike_code="BIKE001")
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    return b
