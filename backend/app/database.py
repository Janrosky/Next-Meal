import sqlite3
import tempfile
import zipfile
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.migrations import VERSION, upgrade_v2
from app.models import Base


class Database:
    """Owns SQLite connections. Write transactions acquire the lock before reading."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.path.as_posix()}",
            connect_args={"check_same_thread": False, "timeout": 15},
        )
        event.listen(self.engine, "connect", self._configure_connection)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    @staticmethod
    def _configure_connection(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    def initialize(self):
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL")
            version = connection.exec_driver_sql("PRAGMA user_version").scalar_one()
            if version not in (0, 1, VERSION):
                raise RuntimeError("Versión de base de datos no compatible.")
        if version == 1:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
            self.backup(self.path.parent / "backups" / f"pre-upgrade-v1-{stamp}.sqlite3")
        with self.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                if version == 1:
                    upgrade_v2(connection)
                Base.metadata.create_all(connection)
                connection.exec_driver_sql(f"PRAGMA user_version={VERSION}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @contextmanager
    def read(self) -> Iterator[Session]:
        with self.sessions() as session:
            yield session

    @contextmanager
    def write(self) -> Iterator[Session]:
        with self.sessions() as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def backup(self, target: Path):
        target = target.resolve()
        if target == self.path:
            raise ValueError("El respaldo debe usar otro archivo.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with (
            closing(sqlite3.connect(self.path)) as source,
            closing(sqlite3.connect(target)) as destination,
        ):
            source.backup(destination)

    def close(self):
        self.engine.dispose()

    def backup_bundle(self, target: Path):
        """Snapshot the database before copying immutable local image files."""
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(".partial")
        try:
            with tempfile.TemporaryDirectory() as folder:
                snapshot = Path(folder) / "soda.sqlite3"
                self.backup(snapshot)
                with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.write(snapshot, "soda.sqlite3")
                    media = self.path.parent / "media"
                    if media.is_dir():
                        for file in media.glob("*.webp"):
                            archive.write(file, "media/" + file.name)
                    archive.writestr(
                        "RESTORE.txt",
                        "Detener el servidor. Extraer en una carpeta nueva. "
                        "Apuntar SODA_DATABASE a soda.sqlite3. Conservar media junto a la base. "
                        "Reiniciar con una versión compatible y verificar los datos.",
                    )
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
