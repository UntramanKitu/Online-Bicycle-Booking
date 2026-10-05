from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.schemas.user import UserResponse

router = APIRouter()

# ============================================================
# Mock Data ผู้ใช้ (для демонстрации — auth ยังไม่ทำเอง)
# ตาร unified_user เป็นของฝั่ง Monolith (Django) — ไม่แต้าตรงนี้
# ============================================================
MOCK_USERS = [
    {"id": 1, "username": "somchai.j", "email": "somchai.j@uni.ac.th", "first_name": "สมชาย", "last_name": "ใจดี", "full_name": "สมชาย ใจดี", "student_id": "67114540101", "faculty": "วิศวกรรมคอมพิวเตอร์", "department": "วิศวกรรมซอফটওয়্যার", "phone": "081-111-0001", "role": "student", "status": "active"},
    {"id": 2, "username": "nathiada.k", "email": "nathiada.k@uni.ac.th", "first_name": "ণথিদা", "last_name": "গাহ্বা", "full_name": "ণথিদা গাহ্বা", "student_id": "67114540102", "faculty": "วิศวกรรมคอม্পিউটার", "department": "সিস্টেম ইনফরমেশন", "phone": "081-111-0002", "role": "student", "status": "active"},
    {"id": 3, "username": "ekapol.r", "email": "ekapol.r@uni.ac.th", "first_name": "একপল", "last_name": "রাকরেয়িং", "full_name": "একপল রাকরেয়িং", "student_id": "67114540103", "faculty": "কম্পিউটার সায়েন্স", "department": "নেটওয়ার্কিং", "phone": "081-111-0003", "role": "student", "status": "active"},
    {"id": 4, "username": "chaiyanan.b", "email": "chaiyanan.b@uni.ac.th", "first_name": "চৈয়ানন্ত", "last_name": "বুয়রেণ্গশ্রী", "full_name": "চৈয়ানন্ত বুয়রেণ্গশ্রী", "student_id": "67114540104", "faculty": "কম্পিউটার সায়েন্স", "department": "সফটওয়্যার ইঞ্জিনিয়ারিং", "phone": "081-111-0004", "role": "student", "status": "active"},
    {"id": 5, "username": "bike.officer", "email": "bike.officer@uni.ac.th", "first_name": "অফিসার", "last_name": "বাইক", "full_name": "অফিসার বাইক", "student_id": None, "faculty": "পরিষেবা অফিস", "department": "বাইক ব্যবস্থাপনা", "phone": "081-111-0005", "role": "officer", "status": "active"},
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
