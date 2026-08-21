from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..persistence.database import Database


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(database: Annotated[Database, Depends(get_database)]) -> Iterator[Session]:
    with database.session() as session:
        yield session


DatabaseDependency = Annotated[Database, Depends(get_database)]
SessionDependency = Annotated[Session, Depends(get_session)]
