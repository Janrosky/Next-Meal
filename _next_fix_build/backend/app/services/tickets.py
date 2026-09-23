from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Business, Customer, Ticket, TicketEvent
from app.schemas import TicketCreate, TicketRead, TicketUpdate


def serialize(ticket: Ticket) -> TicketRead:
    return TicketRead(
        id=ticket.id,
        code=ticket.code,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer.name,
        customer_phone=ticket.customer.phone,
        asset_type=ticket.asset_type,
        brand=ticket.brand,
        model=ticket.model,
        serial_number=ticket.serial_number,
        issue=ticket.issue,
        diagnosis=ticket.diagnosis,
        status=ticket.status,
        priority=ticket.priority,
        assigned_to=ticket.assigned_to,
        estimated_at=ticket.estimated_at,
        labor_cents=ticket.labor_cents,
        parts_cents=ticket.parts_cents,
        paid_cents=ticket.paid_cents,
        notes=ticket.notes,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


class TicketService:
    def list(self, session: Session, search: str = "", status: str = "") -> list[TicketRead]:
        query = select(Ticket).options(joinedload(Ticket.customer)).order_by(Ticket.updated_at.desc())
        if status:
            query = query.where(Ticket.status == status)
        if search.strip():
            value = f"%{search.strip()}%"
            query = query.join(Ticket.customer).where(
                or_(
                    Ticket.code.ilike(value),
                    Ticket.brand.ilike(value),
                    Ticket.model.ilike(value),
                    Ticket.serial_number.ilike(value),
                    Customer.name.ilike(value),
                    Customer.phone.ilike(value),
                )
            )
        return [serialize(ticket) for ticket in session.scalars(query).all()]

    def create(self, session: Session, data: TicketCreate) -> TicketRead:
        customer = session.get(Customer, data.customer_id)
        if customer is None:
            raise ValueError("El cliente seleccionado no existe.")
        business = session.get(Business, 1)
        ticket = Ticket(code="PENDING", **data.model_dump())
        session.add(ticket)
        session.flush()
        prefix = (business.ticket_prefix if business else "NF").upper()
        ticket.code = f"{prefix}-{datetime.now(UTC).year}-{ticket.id:04d}"
        session.add(TicketEvent(ticket_id=ticket.id, event_type="created", summary="Ticket recibido"))
        session.commit()
        session.refresh(ticket)
        ticket.customer = customer
        return serialize(ticket)

    def get(self, session: Session, ticket_id: int) -> Ticket:
        ticket = session.scalar(
            select(Ticket).options(joinedload(Ticket.customer)).where(Ticket.id == ticket_id)
        )
        if ticket is None:
            raise LookupError("El ticket no existe.")
        return ticket

    def update(self, session: Session, ticket_id: int, data: TicketUpdate) -> TicketRead:
        ticket = self.get(session, ticket_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(ticket, key, value)
        ticket.updated_at = datetime.now(UTC)
        session.add(TicketEvent(ticket_id=ticket.id, event_type="updated", summary="Información actualizada"))
        session.commit()
        session.refresh(ticket)
        return serialize(ticket)

    def set_status(self, session: Session, ticket_id: int, status: str) -> TicketRead:
        ticket = self.get(session, ticket_id)
        ticket.status = status
        ticket.updated_at = datetime.now(UTC)
        session.add(TicketEvent(ticket_id=ticket.id, event_type="status", summary=f"Estado: {status}"))
        session.commit()
        session.refresh(ticket)
        return serialize(ticket)
