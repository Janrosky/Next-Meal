import json
import time

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record(session: Session, user_id: int | None, action: str, entity_id: int | str, **details):
    session.add(
        AuditEvent(
            user_id=user_id,
            action=action,
            entity_id=str(entity_id),
            details=json.dumps(details, ensure_ascii=False),
            created_at=int(time.time()),
        )
    )
