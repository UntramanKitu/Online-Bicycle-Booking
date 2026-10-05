from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.crud.booking import (
    get_ticket, get_tickets, get_tickets_by_user, get_tickets_by_status,
    get_tickets_by_category, get_tickets_by_priority, get_tickets_assigned_to,
    create_ticket, update_ticket, delete_ticket,
)
from app.schemas.booking import (
    SupportTicketCreate, SupportTicketUpdate, SupportTicketResponse,
)
from app.models.booking import SupportTicket
from app.modules.auth.deps import require_admin
from app.models.unified_user import UnifiedUser
from pydantic import BaseModel

router = APIRouter()


class AdminStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


@router.get("/tickets", response_model=List[SupportTicketResponse])
def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if user_id:
        return get_tickets_by_user(db, user_id, skip=skip, limit=limit)
    if status:
        return get_tickets_by_status(db, status, skip=skip, limit=limit)
    if category:
        return get_tickets_by_category(db, category, skip=skip, limit=limit)
    if priority:
        return get_tickets_by_priority(db, priority, skip=skip, limit=limit)
    if assigned_to:
        return get_tickets_assigned_to(db, assigned_to, skip=skip, limit=limit)
    return get_tickets(db, skip=skip, limit=limit)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@router.post("/tickets", response_model=SupportTicketResponse, status_code=201)
def create_new_ticket(ticket: SupportTicketCreate, db: Session = Depends(get_db)):
    return create_ticket(db, ticket)


@router.put("/tickets/{ticket_id}", response_model=SupportTicketResponse)
def update_existing_ticket(ticket_id: int, ticket: SupportTicketUpdate, db: Session = Depends(get_db)):
    db_ticket = update_ticket(db, ticket_id, ticket)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@router.delete("/tickets/{ticket_id}", status_code=204)
def delete_existing_ticket(
    ticket_id: int,
    user_id: Optional[int] = Query(None, description="ID เจ้าของคำร้อง"),
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_ticket(db, ticket_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return None


# ==================== Admin-only endpoints ====================

@router.patch("/admin/tickets/{ticket_id}/status", response_model=SupportTicketResponse)
def admin_update_ticket_status(
    ticket_id: int,
    body: AdminStatusUpdate,
    db: Session = Depends(get_db),
    _admin: UnifiedUser = Depends(require_admin),
):
    """[แอดมินเท่านั้น] เปลี่ยนสถานะ ticket ได้ทุกสถานะ เช่น resolved / closed"""
    valid = {"open", "in_progress", "resolved", "closed", "reopened"}
    if body.status not in valid:
        raise HTTPException(status_code=422, detail=f"status ต้องเป็นหนึ่งใน {valid}")
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db_ticket.status = body.status
    if body.resolution_notes is not None:
        db_ticket.resolution_notes = body.resolution_notes
    if body.status in {"resolved", "closed"} and db_ticket.resolved_at is None:
        db_ticket.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.delete("/admin/tickets/{ticket_id}", status_code=204)
def admin_delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _admin: UnifiedUser = Depends(require_admin),
):
    """[แอดมินเท่านั้น] ลบ ticket ได้ทันทีโดยไม่ต้องเช็คสถานะหรือ ownership"""
    db_ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(db_ticket)
    db.commit()
    return None


@router.delete("/admin/tickets", status_code=200)
def admin_bulk_delete_tickets(
    status: Optional[str] = Query(None, description="ลบ ticket ที่มีสถานะนี้ทั้งหมด เช่น closed, resolved"),
    db: Session = Depends(get_db),
    _admin: UnifiedUser = Depends(require_admin),
):
    """[แอดมินเท่านั้น] ลบ ticket หลายรายการพร้อมกัน — ต้องระบุ status เสมอ"""
    if not status:
        raise HTTPException(status_code=422, detail="ต้องระบุ status ที่ต้องการลบ เช่น ?status=closed")
    rows = db.query(SupportTicket).filter(SupportTicket.status == status).all()
    count = len(rows)
    for row in rows:
        db.delete(row)
    db.commit()
    return {"deleted": count, "status": status}