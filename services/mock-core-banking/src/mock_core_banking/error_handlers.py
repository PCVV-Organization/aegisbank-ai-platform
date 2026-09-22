import logging

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from .correlation import CORRELATION_ID_HEADER, get_correlation_id
from .domain.errors import DomainError

logger = logging.getLogger(__name__)


def _build_error_response(code: str, message: str, correlation_id: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "correlation_id": correlation_id}}


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    correlation_id = get_correlation_id(request)
    return JSONResponse(
        status_code=status_code,
        content=_build_error_response(code, message, correlation_id),
        headers={CORRELATION_ID_HEADER: correlation_id},
    )


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        return await generic_exception_handler(request, exc)
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


async def validation_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    if not isinstance(_exc, RequestValidationError):
        return await generic_exception_handler(request, _exc)
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        return await generic_exception_handler(request, exc)
    public_errors = {
        404: ("ROUTE_NOT_FOUND", "Route was not found."),
        405: ("METHOD_NOT_ALLOWED", "HTTP method is not allowed for this route."),
    }
    code, message = public_errors.get(exc.status_code, ("HTTP_ERROR", "HTTP request failed."))
    return _error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = get_correlation_id(request)
    logger.error(
        "Unhandled API exception (correlation_id=%s)",
        correlation_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
    )
