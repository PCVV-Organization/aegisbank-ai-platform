from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from ..persistence.repositories import CustomerRepository, ServiceRequestRepository
from ..schemas import ErrorEnvelope, ServiceRequestCreate, ServiceRequestResponse
from .dependencies import SessionDependency

router = APIRouter(prefix="/api/v1/service-requests", tags=["service-requests"])
ServiceRequestPath = Annotated[str, Path(pattern=r"^SR-[0-9]{6}$")]
CustomerIdQuery = Annotated[str, Query(pattern=r"^CUST-[0-9]{4}$")]


@router.get(
    "",
    response_model=list[ServiceRequestResponse],
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic customer not found"},
        422: {"model": ErrorEnvelope, "description": "Query validation failed"},
    },
)
def list_service_requests(
    customer_id: CustomerIdQuery,
    session: SessionDependency,
) -> list[ServiceRequestResponse]:
    """List requests for one customer; the Agent supplies the authenticated owner."""
    CustomerRepository(session).get_by_id(customer_id)
    records = ServiceRequestRepository(session).list_by_customer(customer_id)
    return [ServiceRequestResponse.model_validate(record) for record in records]


@router.get(
    "/customer/{customer_id}",
    response_model=list[ServiceRequestResponse],
    responses={404: {"model": ErrorEnvelope, "description": "Synthetic customer not found"}},
)
def list_customer_service_requests(
    customer_id: str,
    session: SessionDependency,
) -> list[ServiceRequestResponse]:
    """Return the authoritative request feed for one synthetic customer.

    The Agent API is the authenticated caller of this internal boundary; the
    browser must never call this route or choose the customer identity.
    """
    CustomerRepository(session).get_by_id(customer_id)
    records = ServiceRequestRepository(session).list_by_customer(customer_id)
    return [ServiceRequestResponse.model_validate(record) for record in records]


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
