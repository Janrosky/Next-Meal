from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Business, Customer, Ticket
from app.schemas import (
    BusinessUpdate,
    CustomerCreate,
    CustomerRead,
    StatusUpdate,
    TicketCreate,
    TicketRead,
    TicketUpdate,
)
from app.services.tickets import TicketService

router = APIRouter(prefix="/api")
tickets = TicketService()


def get_session(request: Request):
    yield from request.app.state.database.session()


@router.get("/health")
def health():
    return {"status": "ok", "product": "Next-Fix"}


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(search: str = "", status: str = "", session: Session = Depends(get_session)):
    return tickets.list(session, search, status)


@router.post("/tickets", response_model=TicketRead, status_code=201)
def create_ticket(data: TicketCreate, session: Session = Depends(get_session)):
    try:
        return tickets.create(session, data)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@router.patch("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, session: Session = Depends(get_session)):
    try:
        return tickets.update(session, ticket_id, data)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.post("/tickets/{ticket_id}/status", response_model=TicketRead)
def update_status(ticket_id: int, data: StatusUpdate, session: Session = Depends(get_session)):
    try:
        return tickets.set_status(session, ticket_id, data.status)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(search: str = "", session: Session = Depends(get_session)):
    query = select(Customer).order_by(Customer.name)
    if search.strip():
        value = f"%{search.strip()}%"
        query = query.where(or_(Customer.name.ilike(value), Customer.phone.ilike(value)))
    return session.scalars(query).all()


@router.post("/customers", response_model=CustomerRead, status_code=201)
def create_customer(data: CustomerCreate, session: Session = Depends(get_session)):
    customer = Customer(**data.model_dump())
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@router.get("/business")
def get_business(session: Session = Depends(get_session)):
    return session.get(Business, 1)


@router.patch("/business")
def update_business(data: BusinessUpdate, session: Session = Depends(get_session)):
    business = session.get(Business, 1)
    for key, value in data.model_dump().items():
        setattr(business, key, value)
    session.commit()
    session.refresh(business)
    return business


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    active_statuses = ("received", "diagnosing", "approval", "repairing", "ready")
    counts = dict(session.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all())
    active = sum(counts.get(status, 0) for status in active_statuses)
    urgent = session.scalar(select(func.count(Ticket.id)).where(Ticket.priority == "urgent", Ticket.status != "delivered")) or 0
    today = datetime.now(UTC).date()
    delivered_today = session.scalar(select(func.count(Ticket.id)).where(Ticket.status == "delivered", func.date(Ticket.updated_at) == today.isoformat())) or 0
    revenue = session.scalar(select(func.sum(Ticket.paid_cents))) or 0
    return {
        "active": active,
        "ready": counts.get("ready", 0),
        "urgent": urgent,
        "delivered_today": delivered_today,
        "revenue_cents": revenue,
        "status_counts": {status: counts.get(status, 0) for status in (*active_statuses, "delivered")},
        "recent": tickets.list(session)[:5],
    }
