"""อัปโหลดรูปภาพ (ใช้แนบตอนแจ้งซ่อม M14)

เก็บไฟล์ที่ backend/uploads/ แล้วเสิร์ฟกลับผ่าน static mount `/api/uploads/<filename>`
(ต้อง mount ใต้ /api ด้วย เพราะ vite dev server proxy เฉพาะ /api ไปที่ backend)
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

# backend/app/routers/uploads.py → backend/uploads/
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """อัปโหลดรูปภาพเดียว → คืน {filename, url} (url เอาไปใส่ใน maintenance_reports.images)"""
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="อัปโหลดได้เฉพาะไฟล์รูปภาพเท่านั้น")
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ .jpg .jpeg .png .webp .gif เท่านั้น",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="ไฟล์ว่างเปล่า")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ขนาดไฟล์ต้องไม่เกิน 5 MB")
    filename = f"{uuid.uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / filename).write_bytes(data)
    return {"filename": filename, "url": f"/api/uploads/{filename}"}
