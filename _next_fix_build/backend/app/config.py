import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    static_path: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[2]
        return cls(
            database_path=Path(os.getenv("NEXTFIX_DATABASE", project_root / "data" / "nextfix.sqlite3")),
            static_path=Path(os.getenv("NEXTFIX_STATIC", project_root / "frontend" / "dist")),
        )
