from typing import Annotated

from fastapi import APIRouter, Path, Response, status

from ..persistence.repositories import CustomerRepository, ServiceRequestRepository
from ..schemas import ErrorEnvelope, ServiceRequestCreate, ServiceRequestResponse
from .dependencies import SessionDependency

router = APIRouter(prefix="/api/v1/service-requests", tags=["service-requests"])
ServiceRequestPath = Annotated[str, Path(pattern=r"^SR-[0-9]{6}$")]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ServiceRequestResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic customer not found"},
        422: {"model": ErrorEnvelope, "description": "Request validation failed"},
    },
)
def create_service_request(
    payload: ServiceRequestCreate,
    response: Response,
    session: SessionDependency,
) -> ServiceRequestResponse:
    # The transaction context commits on success and rolls back any raised failure.
    with session.begin():
        CustomerRepository(session).get_by_id(payload.customer_id)
        record = ServiceRequestRepository(session).create(
            customer_id=payload.customer_id,
            category=payload.category,
            description=payload.description,
        )
        result = ServiceRequestResponse.model_validate(record)

    response.headers["Location"] = f"/api/v1/service-requests/{result.service_request_id}"
    return result


@router.get(
    "/{service_request_id}",
    response_model=ServiceRequestResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic service request not found"},
        422: {"model": ErrorEnvelope, "description": "Path validation failed"},
    },
)
def get_service_request(
    service_request_id: ServiceRequestPath,
    session: SessionDependency,
) -> ServiceRequestResponse:
    record = ServiceRequestRepository(session).get_by_id(service_request_id)
    return ServiceRequestResponse.model_validate(record)
