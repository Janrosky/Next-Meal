import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from sqlalchemy import delete, select

from app.database import Database
from app.domain import BusinessError, Principal, Role
from app.models import AuthSession, User

PASSWORD_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256$ {PASSWORD_ITERATIONS}$ {salt}$ {digest}".replace("$ ", "$")


def verify_password(password: str, encoded: str) -> bool:
    algorithm, iterations, salt, expected = encoded.split("$")
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
    ).hex()
    return hmac.compare_digest(actual, expected)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AttemptLimiter:
    def __init__(self, limit: int = 10, window: int = 300):
        self.limit = limit
        self.window = window
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str):
        now = time.monotonic()
        with self._lock:
            expired = [
                key
                for key, values in self._attempts.items()
                if not values or values[-1] <= now - self.window
            ]
            for stale in expired:
                del self._attempts[stale]
            attempts = self._attempts[key]
            while attempts and attempts[0] <= now - self.window:
                attempts.popleft()
            if len(attempts) >= self.limit:
                raise BusinessError("Demasiados intentos. Esperá cinco minutos.", 429)
            attempts.append(now)


class AuthService:
    def __init__(self, database: Database, session_hours: int):
        self.database = database
        self.session_hours = session_hours
        self.limiter = AttemptLimiter()
        self.dummy_hash = hash_password(secrets.token_urlsafe(24))

    def login(self, username: str, password: str, address: str) -> dict:
        self.limiter.check(address)
        with self.database.read() as session:
            user = session.scalar(select(User).where(User.username == username))
            encoded = user.password_hash if user else self.dummy_hash
            valid = verify_password(password, encoded)
            if not valid or not user or not user.active:
                raise BusinessError("Usuario o contraseña incorrectos.", 401)
            user_id, password_hash = user.id, user.password_hash
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        with self.database.write() as session:
            user = session.get(User, user_id)
            if not user or not user.active or user.password_hash != password_hash:
                raise BusinessError("La cuenta cambió. Iniciá sesión de nuevo.", 401)
            session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
            session.add(
                AuthSession(
                    token_hash=token_hash(token),
                    user_id=user.id,
                    expires_at=now + self.session_hours * 3600,
                )
            )
            return {"token": token, "user": user_view(user)}

    def authenticate(self, token: str) -> Principal:
        with self.database.read() as session:
            auth = session.get(AuthSession, token_hash(token))
            if not auth or auth.expires_at <= int(time.time()) or not auth.user.active:
                raise BusinessError("La sesión venció. Iniciá sesión de nuevo.", 401)
            return Principal(auth.user.id, auth.user.username, Role(auth.user.role))

    def logout(self, token: str):
        with self.database.write() as session:
            session.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))


def user_view(user: User) -> dict:
    return {"id": user.id, "username": user.username, "role": user.role, "active": user.active}
