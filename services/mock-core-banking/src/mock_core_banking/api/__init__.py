from .customers import router as customers_router
from .health import router as health_router
from .loans import router as loans_router
from .service_requests import router as service_requests_router

__all__ = [
    "health_router",
    "customers_router",
    "loans_router",
    "service_requests_router",
]
