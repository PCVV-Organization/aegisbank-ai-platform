from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from . import __version__
from .api import customers, health, loans, service_requests
from .config import Settings
from .correlation import CorrelationMiddleware
from .domain.errors import DomainError
from .error_handlers import (
    domain_error_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_error_handler,
)
from .persistence.database import Database
from .persistence.seed import seed_database


def create_app(settings: Settings | None = None) -> FastAPI:
    effective_settings = settings or Settings.from_environment()
    database = Database(effective_settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        database.create_schema()
        seed_database(database)
        try:
            yield
        finally:
            database.dispose()

    application = FastAPI(
        title="AegisBank Mock Core Banking API",
        version=__version__,
        description="Local educational API backed only by deterministic synthetic data.",
        lifespan=lifespan,
    )
    application.state.database = database
    application.state.settings = effective_settings
    application.add_middleware(CorrelationMiddleware)
    application.add_exception_handler(DomainError, domain_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(Exception, generic_exception_handler)
    application.include_router(health.router)
    application.include_router(customers.router)
    application.include_router(loans.router)
    application.include_router(service_requests.router)
    return application


app = create_app()
