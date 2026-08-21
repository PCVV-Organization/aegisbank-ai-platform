import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = SERVICE_ROOT / "data" / "local" / "aegisbank-dev.db"


def default_database_url() -> str:
    return f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    environment: str = Field(default="development", pattern=r"^[a-z][a-z0-9_-]{1,31}$")
    database_url: str = Field(default_factory=default_database_url, min_length=1)

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            environment=os.getenv("AEGISBANK_ENV", "development").strip().lower(),
            database_url=os.getenv("AEGISBANK_DATABASE_URL", default_database_url()),
        )
