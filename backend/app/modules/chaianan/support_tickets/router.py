from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.booking import (
    get_ticket, get_tickets, get_tickets_by_user, get_tickets_by_status,
    get_tickets_by_category, get_tickets_by_priority, get_tickets_assigned_to,
    create_ticket, update_ticket, delete_ticket,
)
from app.schemas.booking import (
    SupportTicketCreate, SupportTicketUpdate, SupportTicketResponse,
)

router = APIRouter()


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