from typing import Optional, Tuple

from fastapi import Header, HTTPException

from models import UnifiedUser, Bicycle


# ==================== ระบุตัวตนแบบง่าย (ยังไม่มี login/รหัสผ่านจริง) ====================
#
# ทีม Django (Back Office) ยังไม่ได้ทำระบบ login ที่ frontend ฝั่งนี้เรียกใช้ได้ ระหว่างรอ
# ใช้วิธีนี้ไปก่อน: หน้าเว็บให้คนกด "ยืนยันตัวตน" ว่าตัวเองคือ user คนไหน แล้วแนบมากับทุก
# request เป็น header ธรรมดา — ไม่ได้ยืนยันด้วยรหัสผ่านจริง ป้องกันการกดพลาด/แก้ผิดคนใน
# หน้าเว็บได้ แต่ป้องกันคนที่ตั้งใจปลอม header ไม่ได้ 100% (ต้องรอ login จริงถึงจะปิดช่องนี้)
Actor = Tuple[str, Optional[int]]  # (role, user_id) — role คือ "user" หรือ "admin"


def get_actor(
    x_actor_role: str = Header(default="user", alias="X-Actor-Role"),
    x_actor_user_id: Optional[str] = Header(default=None, alias="X-Actor-User-Id"),
) -> Actor:
    role = x_actor_role if x_actor_role in ("user", "admin") else "user"  # ค่าเริ่มต้นปลอดภัยไว้ก่อน
    actor_id = None
    if x_actor_user_id:
        try:
            actor_id = int(x_actor_user_id)
        except ValueError:
            actor_id = None
    return role, actor_id


def require_owner_or_admin(record_user_id: int, actor: Actor) -> None:
    """ใช้ก่อนแก้ไข/ลบ record ที่มีเจ้าของ — โหมดแอดมินผ่านได้เสมอ โหมดผู้ใช้ต้องเป็นเจ้าของเท่านั้น"""
    role, actor_id = actor
    if role == "admin":
        return
    if actor_id is None or actor_id != record_user_id:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ทำรายการนี้ — แก้ไข/ลบได้เฉพาะของตัวเองเท่านั้น")


def require_admin(actor: Actor) -> None:
    """ใช้กับ endpoint ที่เป็นสิทธิ์แอดมินล้วนๆ (เช่น ออกบทลงโทษ)"""
    role, _ = actor
    if role != "admin":
        raise HTTPException(status_code=403, detail="ต้องเป็นแอดมินเท่านั้นถึงจะทำรายการนี้ได้")


def resolve_user(user_val, db):
    # ต้องลองแปลงเป็นเลขก่อนแล้วค่อย query แยกกัน (เหมือน resolve_bicycle ด้านล่าง) ห้าม
    # เทียบ id (คอลัมน์ integer) กับ string ในเงื่อนไข OR เดียวกัน เพราะ Postgres เข้มงวด
    # เรื่องชนิดข้อมูล — ถ้า user_val เป็น "user001" จะพัง (InvalidTextRepresentation) ทันที
    # ตอนพยายามแปลง "user001" เป็น int ให้คอลัมน์ id (SQLite ปล่อยผ่านเพราะไม่เข้มงวดเท่า
    # เลยไม่เจอบั๊กนี้ตอนรันเทสด้วย SQLite)
    try:
        user_id = int(user_val)
        user = db.query(UnifiedUser).filter(UnifiedUser.id == user_id).first()
    except (ValueError, TypeError):
        user = db.query(UnifiedUser).filter(UnifiedUser.username == str(user_val)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def resolve_bicycle(bike_val, db):
    try:
        bike_id = int(bike_val)
        bike = db.query(Bicycle).filter(Bicycle.id == bike_id).first()
    except ValueError:
        bike = db.query(Bicycle).filter(Bicycle.bike_code == str(bike_val)).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Bicycle not found")
    return bike
