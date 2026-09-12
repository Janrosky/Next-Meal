import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_path: Path
    static_path: Path
    session_hours: int = 8

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            database_path=Path(os.getenv("SODA_DATABASE", PROJECT_ROOT / "data" / "soda.sqlite3")),
            static_path=Path(os.getenv("SODA_STATIC", PROJECT_ROOT / "frontend" / "dist")),
        )
