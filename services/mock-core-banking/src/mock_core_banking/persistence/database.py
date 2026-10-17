from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from . import models as _models  # noqa: F401
from .base import Base


def _build_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
    if url.get_backend_name() == "sqlite":
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if not url.database or url.database == ":memory:":
            engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_kwargs)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record):
        if url.get_backend_name() == "sqlite":
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


class Database:
    def __init__(self, database_url: str):
        ensure_sqlite_parent(database_url)
        self._engine = _build_engine(database_url)
        self.session_factory = sessionmaker(
            bind=self._engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            yield session

    def create_schema(self) -> None:
        Base.metadata.create_all(bind=self.engine)
        if self.engine.dialect.name == "sqlite":
            with self.engine.begin() as connection:
                columns = {
                    row[1]
                    for row in connection.execute(text("PRAGMA table_info(service_requests)"))
                }
                if "reason_code" not in columns:
                    connection.execute(
                        text(
                            "ALTER TABLE service_requests ADD COLUMN reason_code "
                            "VARCHAR(64) NOT NULL DEFAULT 'GENERAL_OTHER'"
                        )
                    )
                if "reason_label" not in columns:
                    connection.execute(
                        text(
                            "ALTER TABLE service_requests ADD COLUMN reason_label "
                            "VARCHAR(120) NOT NULL DEFAULT 'Otro motivo'"
                        )
                    )

    def is_ready(self) -> bool:
        try:
            with self.session_factory() as session:
                session.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def dispose(self) -> None:
        self._engine.dispose()


def ensure_sqlite_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
