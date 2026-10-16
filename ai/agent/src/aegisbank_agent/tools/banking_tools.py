"""Read-only function tools for mock core banking operations."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from mock_core_banking.domain.enums import ServiceRequestCategory
from mock_core_banking.domain.errors import CustomerNotFoundError, LoanNotFoundError
from mock_core_banking.domain.next_installment import select_next_installment
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.repositories import (
    CustomerRepository,
    InstallmentRepository,
    LoanRepository,
    ServiceRequestRepository,
)
from mock_core_banking.persistence.seed import seed_database

from .base import AgentContext, FunctionTool, ToolResult

LOAN_ID_PATTERN: re.Pattern[str] = re.compile(r"^LOAN-[0-9]{4}$")


def create_default_database() -> Database:
    """Create and seed an in-memory or configured database with synthetic banking data."""
    from aegisbank_agent.configuration.environment import resolve_runtime_environment

    env = resolve_runtime_environment()
    db_url = os.getenv("AEGISBANK_DATABASE_URL")
    if env.is_cloud and db_url:
        raise RuntimeError(
            "Direct Core Banking database access is prohibited in cloud environments; "
            "Agent must interact via Core Banking API boundary"
        )
    if db_url:
        db = Database(db_url)
        db.create_schema()
        seed_database(db)
        return db
    db = Database("sqlite:///:memory:")
    db.create_schema()
    seed_database(db)
    return db


class GetMyLoansTool(FunctionTool):
    """Tool to list all loans for the authenticated session customer."""

    def __init__(self, database: Database | None = None) -> None:
        self._db = database or create_default_database()

    @property
    def name(self) -> str:
        return "get_my_loans"

    @property
    def description(self) -> str:
        return (
            "Obtiene la lista de todos los préstamos pertenecientes al cliente "
            "autenticado en la sesión."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        with self._db.session() as session:
            try:
                CustomerRepository(session).get_by_id(context.session_customer_id)
                loans = LoanRepository(session).list_by_customer(context.session_customer_id)
            except CustomerNotFoundError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Cliente {context.session_customer_id} no encontrado en el sistema.",
                )

            formatted_loans = [
                {
                    "loan_id": loan.loan_id,
                    "product_code": loan.product_code,
                    "currency": loan.currency.value,
                    "principal_amount": str(loan.principal_amount),
                    "outstanding_balance": str(loan.outstanding_balance),
                    "status": loan.status.value,
                    "opened_at": loan.opened_at.isoformat(),
                }
                for loan in loans
            ]
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "customer_id": context.session_customer_id,
                    "loans": formatted_loans,
                    "total_loans": len(formatted_loans),
                },
            )


class GetAccountBalanceTool(FunctionTool):
    """Return the synthetic available balance for the authenticated customer."""

    _BALANCES = {
        "CUST-0001": ("12480.00", "PEN"),
        "CUST-0002": ("8650.00", "PEN"),
    }

    @property
    def name(self) -> str:
        return "get_account_balance"

    @property
    def description(self) -> str:
        return "Obtiene el saldo disponible sintético del cliente autenticado."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        balance = self._BALANCES.get(context.session_customer_id)
        if balance is None:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Cliente no encontrado en el sistema bancario sintético.",
            )
        amount, currency = balance
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "customer_id": context.session_customer_id,
                "available_balance": amount,
                "currency": currency,
            },
        )


class GetLoanDetailsTool(FunctionTool):
    """Tool to inspect specific loan details with customer ownership validation."""

    def __init__(self, database: Database | None = None) -> None:
        self._db = database or create_default_database()

    @property
    def name(self) -> str:
        return "get_loan_details"

    @property
    def description(self) -> str:
        return (
            "Obtiene el detalle completo (saldos, estado, montos) de un préstamo específico "
            "perteneciente al cliente de la sesión."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "loan_id": {
                    "type": "string",
                    "description": "Identificador único del préstamo (formato: LOAN-XXXX).",
                }
            },
            "required": ["loan_id"],
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        loan_id = arguments.get("loan_id")
        if not isinstance(loan_id, str) or not LOAN_ID_PATTERN.match(loan_id):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="El parámetro 'loan_id' debe tener un formato válido como 'LOAN-0001'.",
            )

        with self._db.session() as session:
            try:
                loan = LoanRepository(session).get_by_id(loan_id)
            except LoanNotFoundError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Préstamo '{loan_id}' no encontrado.",
                )

            # Deterministic customer ownership check
            if loan.customer_id != context.session_customer_id:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=(
                        f"Acceso denegado: El préstamo '{loan_id}' no pertenece "
                        f"al cliente autenticado ({context.session_customer_id})."
                    ),
                )

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "loan_id": loan.loan_id,
                    "customer_id": loan.customer_id,
                    "product_code": loan.product_code,
                    "currency": loan.currency.value,
                    "principal_amount": str(loan.principal_amount),
                    "outstanding_balance": str(loan.outstanding_balance),
                    "status": loan.status.value,
                    "opened_at": loan.opened_at.isoformat(),
                },
            )


class GetNextInstallmentTool(FunctionTool):
    """Tool to inspect the next installment schedule for a customer loan."""

    def __init__(self, database: Database | None = None) -> None:
        self._db = database or create_default_database()

    @property
    def name(self) -> str:
        return "get_next_installment"

    @property
    def description(self) -> str:
        return (
            "Obtiene los datos de la próxima cuota a pagar (monto total, fecha de vencimiento, "
            "interés y estado) de un préstamo perteneciente al cliente de la sesión."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "loan_id": {
                    "type": "string",
                    "description": "Identificador único del préstamo (formato: LOAN-XXXX).",
                }
            },
            "required": ["loan_id"],
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        loan_id = arguments.get("loan_id")
        if not isinstance(loan_id, str) or not LOAN_ID_PATTERN.match(loan_id):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="El parámetro 'loan_id' debe tener un formato válido como 'LOAN-0001'.",
            )

        with self._db.session() as session:
            try:
                loan = LoanRepository(session).get_by_id(loan_id)
            except LoanNotFoundError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Préstamo '{loan_id}' no encontrado.",
                )

            # Deterministic customer ownership check
            if loan.customer_id != context.session_customer_id:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=(
                        f"Acceso denegado: El préstamo '{loan_id}' no pertenece "
                        f"al cliente autenticado ({context.session_customer_id})."
                    ),
                )

            installments = InstallmentRepository(session).list_by_loan(loan_id)
            installment = select_next_installment(installments)
            if installment is None:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "loan_id": loan_id,
                        "has_next_installment": False,
                        "message": "No hay cuotas pendientes ni vencidas para este préstamo.",
                    },
                )

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "loan_id": loan_id,
                    "currency": loan.currency.value,
                    "has_next_installment": True,
                    "installment_id": installment.installment_id,
                    "installment_number": installment.installment_number,
                    "due_date": installment.due_date.isoformat(),
                    "principal_due": str(installment.principal_due),
                    "interest_due": str(installment.interest_due),
                    "fees_due": str(installment.fees_due),
                    "total_due": str(installment.total_due),
                    "status": installment.status.value,
                },
            )


class CreateServiceRequestTool(FunctionTool):
    """Tool to create a synthetic customer service request or claim in Core Banking."""

    def __init__(self, database: Database | None = None) -> None:
        self._db = database or create_default_database()

    @property
    def name(self) -> str:
        return "create_service_request"

    @property
    def description(self) -> str:
        return (
            "Crea una solicitud de servicio o reclamo bancario para el cliente de la sesión. "
            "Requiere aprobación humana explícita antes de su ejecución."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        categories = [c.value for c in ServiceRequestCategory]
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": categories,
                    "description": (
                        f"Categoría canónica de la solicitud o reclamo ({', '.join(categories)})."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Detalle descriptivo del reclamo o solicitud del cliente.",
                },
                "idempotency_key": {
                    "type": "string",
                    "description": "Llave única para garantizar que la solicitud no se duplique.",
                },
            },
            "required": ["category", "description"],
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        raw_category = arguments.get("category")
        description = arguments.get("description")
        idempotency_key = arguments.get("idempotency_key")

        if not isinstance(raw_category, str) or not raw_category.strip():
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="El parámetro 'category' es obligatorio (LOAN, INSTALLMENT, FEE, GENERAL).",
            )

        cat_upper = raw_category.strip().upper()
        cat_map = {
            "CLAIM": ServiceRequestCategory.GENERAL,
            "RECLAMO": ServiceRequestCategory.GENERAL,
            "GENERAL": ServiceRequestCategory.GENERAL,
            "LOAN": ServiceRequestCategory.LOAN,
            "PRESTAMO": ServiceRequestCategory.LOAN,
            "PRÉSTAMO": ServiceRequestCategory.LOAN,
            "INSTALLMENT": ServiceRequestCategory.INSTALLMENT,
            "CUOTA": ServiceRequestCategory.INSTALLMENT,
            "FEE": ServiceRequestCategory.FEE,
            "COMISION": ServiceRequestCategory.FEE,
            "COMISIÓN": ServiceRequestCategory.FEE,
        }
        category_enum = cat_map.get(cat_upper)
        if category_enum is None:
            try:
                category_enum = ServiceRequestCategory(cat_upper)
            except ValueError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=(
                        f"Categoría '{raw_category}' inválida. "
                        "Valores permitidos: LOAN, INSTALLMENT, FEE, GENERAL."
                    ),
                )

        if not isinstance(description, str) or len(description.strip()) < 5:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=(
                    "El parámetro 'description' debe contener al menos 5 caracteres descriptivos."
                ),
            )

        # Normalize arguments for idempotency checking
        normalized_args = {
            "category": category_enum.value,
            "description": description.strip(),
        }
        effective_key = (
            idempotency_key.strip()
            if isinstance(idempotency_key, str) and idempotency_key.strip()
            else None
        )

        core_banking_url = os.getenv("AEGISBANK_CORE_BANKING_URL") or os.getenv("CORE_BANKING_URL")

        def _do_create() -> dict[str, Any]:
            if core_banking_url:
                target_url = f"{core_banking_url.rstrip('/')}/api/v1/service-requests"
                payload_dict = {
                    "customer_id": context.session_customer_id,
                    "category": category_enum.value,
                    "description": description.strip(),
                }
                req_data = json.dumps(payload_dict).encode("utf-8")
                req = urllib.request.Request(
                    target_url,
                    data=req_data,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=10.0) as resp:  # nosec B310 - URL comes from validated configured endpoint
                        resp_body = resp.read().decode("utf-8")
                        return json.loads(resp_body)
                except urllib.error.HTTPError as http_err:
                    err_body = http_err.read().decode("utf-8")
                    try:
                        err_json = json.loads(err_body)
                        msg = (
                            err_json.get("error", {}).get("message")
                            or err_json.get("detail")
                            or str(http_err)
                        )
                    except Exception:
                        msg = str(http_err)
                    raise ValueError(
                        f"Core Banking HTTP error ({http_err.code}): {msg}"
                    ) from http_err
                except Exception as exc:
                    raise ValueError(f"Core Banking HTTP connection failure: {exc}") from exc

            with self._db.session() as session:
                cust_repo = CustomerRepository(session)
                try:
                    cust_repo.get_by_id(context.session_customer_id)
                except CustomerNotFoundError:
                    raise ValueError(
                        f"Cliente '{context.session_customer_id}' no encontrado en Core Banking."
                    )

                sr_repo = ServiceRequestRepository(session)
                sr = sr_repo.create(
                    customer_id=context.session_customer_id,
                    category=category_enum,
                    description=description.strip(),
                )
                session.commit()
                return {
                    "service_request_id": sr.service_request_id,
                    "customer_id": sr.customer_id,
                    "category": sr.category.value,
                    "description": sr.description,
                    "status": sr.status.value,
                    "created_at": sr.created_at.isoformat(),
                }

        try:
            if effective_key:
                from ..reliability.idempotency import (
                    IdempotencyGuard,
                )

                guard = IdempotencyGuard(self._db)
                data, cached = guard.execute_idempotent(
                    idempotency_key=effective_key,
                    customer_id=context.session_customer_id,
                    arguments=normalized_args,
                    operation=_do_create,
                )
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data=data,
                )
            else:
                data = _do_create()
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data=data,
                )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
            )
