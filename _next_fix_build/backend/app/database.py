from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{path}", connect_args={"check_same_thread": False}, future=True
        )
        event.listen(self.engine, "connect", self._configure_sqlite)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @staticmethod
    def _configure_sqlite(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    def initialize(self):
        Base.metadata.create_all(self.engine)

    def session(self) -> Iterator[Session]:
        with self.sessions() as session:
            yield session

    def close(self):
        self.engine.dispose()
