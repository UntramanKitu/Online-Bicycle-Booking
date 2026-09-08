from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import UnifiedUserResponse
from utils import resolve_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/resolve/{user_val}", response_model=UnifiedUserResponse)
def resolve_user_endpoint(user_val: str, db: Session = Depends(get_db)):
    """
    ใช้ตอน "ยืนยันตัวตน" ฝั่งหน้าเว็บ — แปลงค่าที่คนพิมพ์ (username หรือ id ตัวเลข)
    ให้เป็นข้อมูลผู้ใช้จริง (โดยเฉพาะ id ตัวเลข) เพื่อเก็บไว้เทียบเจ้าของข้อมูลตอนแก้/ลบ
    """
    return resolve_user(user_val, db)
