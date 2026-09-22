from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Store UTC consistently and restore timezone data lost by SQLite."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware value.")
        normalized = value.astimezone(timezone.utc)
        if dialect.name == "sqlite":
            return normalized.replace(tzinfo=None)
        return normalized

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
