import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import DamageEvidence
from schemas import DamageEvidenceUpdate, DamageEvidenceResponse

router = APIRouter(prefix="/api/damages", tags=["Damages"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_images(files: List[UploadFile]) -> List[str]:
    saved = []
    for f in files:
        ext = os.path.splitext(f.filename or ".jpg")[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        saved.append(filename)
    return saved


@router.get("/", response_model=List[DamageEvidenceResponse])
def list_damages(db: Session = Depends(get_db)):
    return db.query(DamageEvidence).order_by(DamageEvidence.created_at.desc()).all()


@router.get("/{damage_id}", response_model=DamageEvidenceResponse)
def get_damage(damage_id: int, db: Session = Depends(get_db)):
    record = db.query(DamageEvidence).filter(DamageEvidence.id == damage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Damage record not found")
    return record


@router.post("/", response_model=DamageEvidenceResponse, status_code=201)
async def create_damage(
    return_id: int = Form(...),
    description: str = Form(...),
    severity: str = Form("minor"),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    image_paths = None
    if images:
        saved = _save_images(images)
        image_paths = ",".join(saved)

    record = DamageEvidence(
        return_id=return_id,
        description=description,
        severity=severity,
        image_paths=image_paths,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{damage_id}", response_model=DamageEvidenceResponse)
async def update_damage(
    damage_id: int,
    description: Optional[str] = Form(None),
    severity: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    record = db.query(DamageEvidence).filter(DamageEvidence.id == damage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Damage record not found")

    if description is not None:
        record.description = description
    if severity is not None:
        record.severity = severity
    if images:
        saved = _save_images(images)
        existing = record.image_paths.split(",") if record.image_paths else []
        record.image_paths = ",".join(existing + saved)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{damage_id}", status_code=204)
def delete_damage(damage_id: int, db: Session = Depends(get_db)):
    record = db.query(DamageEvidence).filter(DamageEvidence.id == damage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Damage record not found")

    if record.image_paths:
        for fname in record.image_paths.split(","):
            fpath = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)

    db.delete(record)
    db.commit()
