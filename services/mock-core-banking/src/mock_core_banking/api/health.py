from fastapi import APIRouter

from .. import __version__
from ..domain.errors import DataStoreUnavailableError
from ..schemas import ErrorEnvelope, HealthResponse
from .dependencies import DatabaseDependency

router = APIRouter(prefix="/health", tags=["health"])


def _health_response() -> HealthResponse:
    return HealthResponse(status="ok", service="aegisbank-mock-core", version=__version__)


@router.get("/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return _health_response()


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": ErrorEnvelope, "description": "Local datastore unavailable"}},
)
def health_ready(database: DatabaseDependency) -> HealthResponse:
    if not database.is_ready():
        raise DataStoreUnavailableError()
    return _health_response()
