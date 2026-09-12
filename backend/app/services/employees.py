from sqlalchemy import delete, func, select

from app.database import Database
from app.domain import BusinessError, Principal, Role
from app.models import AuthSession, User
from app.schemas import UserInput, UserUpdate
from app.security import hash_password, user_view
from app.services.audit import record


class EmployeeService:
    def __init__(self, database: Database):
        self.database = database

    def list(self) -> list[dict]:
        with self.database.read() as session:
            return [user_view(u) for u in session.scalars(select(User).order_by(User.username))]

    def create(self, data: UserInput, actor: Principal | None = None) -> dict:
        encoded = hash_password(data.password)
        with self.database.write() as session:
            if session.scalar(select(User).where(User.username == data.username)):
                raise BusinessError("Ese usuario ya existe.", 409)
            user = User(username=data.username, password_hash=encoded, role=data.role)
            session.add(user)
            session.flush()
            record(session, actor.id if actor else user.id, "user.created", user.id, role=user.role)
            return user_view(user)

    def update(self, user_id: int, data: UserUpdate, actor: Principal) -> dict:
        encoded = hash_password(data.password) if data.password else None
        with self.database.write() as session:
            user = session.get(User, user_id)
            if not user:
                raise BusinessError("Usuario no encontrado.", 404)
            if user.id == actor.id and (not data.active or data.role != Role.ADMIN):
                raise BusinessError("No podés quitarte el acceso de administrador.")
            if (
                user.role == Role.ADMIN
                and user.active
                and (data.role != Role.ADMIN or not data.active)
            ):
                admins = session.scalar(
                    select(func.count())
                    .select_from(User)
                    .where(User.role == Role.ADMIN, User.active.is_(True))
                )
                if admins <= 1:
                    raise BusinessError("Debe quedar al menos un administrador activo.")
            changed = user.role != data.role or user.active != data.active or encoded is not None
            user.role, user.active = data.role, data.active
            if encoded:
                user.password_hash = encoded
            if changed:
                session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
            record(session, actor.id, "user.updated", user.id, role=user.role, active=user.active)
            return user_view(user)
