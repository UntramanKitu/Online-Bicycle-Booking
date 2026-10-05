from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.schemas.user import UserResponse

router = APIRouter()

# ============================================================
# Mock Data ผู้ใช้ (ใช้สลับ user ตอน demo — ยังไม่ได้ผูกกับ Django Monolith)
# ชื่ออ้างอ้าษของมาจาก เพิ่ยศสี้อาชาพชรับผิดชอบที่ docs\Database_Schema_v2 (1).md
# ตาราง unified_user เป็นของฝั่งคะของ Django — ฝั่นนี้ยังไม่แต้ตารางนั้น
# ============================================================
_UNI = "uni.ac.th"
_FACULTY = "คณะวิทยศาสตร์"
_DEPARTMENT = "วิทยาการคอมพิวเตอร์"

MOCK_USERS = [
    {
        "id": 1, "username": "piyapong.s", "email": f"piyapong.s@{_UNI}",
        "first_name": "ปิยะพงษ์", "last_name": "สุขใจ", "full_name": "ปิยะพงษ์ สุขใจ",
        "student_id": "67114540101", "faculty": _FACULTY, "department": _DEPARTMENT,
        "role": "student", "status": "active",
    },
    {
        "id": 2, "username": "weerapong.t", "email": f"weerapong.t@{_UNI}",
        "first_name": "วีรพันธ์", "last_name": "ทองแท้", "full_name": "วีรพันธ์ ทองแท้",
        "student_id": "67114540102", "faculty": _FACULTY, "department": _DEPARTMENT,
        "role": "student", "status": "active",
    },
    {
        "id": 3, "username": "ekapol.r", "email": f"ekapol.r@{_UNI}",
        "first_name": "เอกพล", "last_name": "รักเรียน", "full_name": "เอกพล รักเรียน",
        "student_id": "67114540103", "faculty": _FACULTY, "department": _DEPARTMENT,
        "role": "student", "status": "active",
    },
    {
        "id": 4, "username": "nathiada.k", "email": f"nathiada.k@{_UNI}",
        "first_name": "ณธิดา", "last_name": "กาญจน์", "full_name": "ณธิดา กาญจน์",
        "student_id": "67114540104", "faculty": _FACULTY, "department": _DEPARTMENT,
        "role": "student", "status": "active",
    },
    {
        "id": 5, "username": "chaiyanan.b", "email": f"chaiyanan.b@{_UNI}",
        "first_name": "ชัยอนันต์", "last_name": "บุณรังษี", "full_name": "ชัยอนันต์ บุณรังษี",
        "student_id": "67114540105", "faculty": _FACULTY, "department": _DEPARTMENT,
        "role": "student", "status": "active",
    },
    {
        "id": 6, "username": "bike.officer", "email": f"bike.officer@{_UNI}",
        "first_name": "ผู้ดูล", "last_name": "จักรยาน", "full_name": "ผู้ดูลจักรยาน",
        "student_id": None, "faculty": "สำนักงานบริการ", "department": "จัดการจักรยาน",
        "role": "officer", "status": "active",
    },
]


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Mock: รายชื่อผู้ใช้ (frontend ใช้สำหรับเลือกผู้ใช้ปัจจุบัน)"""
    return MOCK_USERS[skip : skip + limit]


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int):
    for user in MOCK_USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")
