"""Hosted HTTP API adapter for AegisBank AgentOrchestrator.

Provides production HTTP endpoints (/health/live, /health/ready, /api/v1/agent/run)
without replacing the existing CLI or MCP stdio interfaces.
Enforces an explicit authentication boundary in cloud environments.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from .agent import AgentExecutionResult, AgentOrchestrator
from .tools.base import AgentContext
from .configuration.environment import (
    EnvironmentSelectionError,
    RuntimeEnvironment,
    resolve_runtime_environment,
    validate_runtime_configuration,
)
from .conversation_store import ConversationStore
from .customer_auth import CosmosAuthStore, CustomerAuth

logger = logging.getLogger("aegisbank.agent.api")


class CustomerLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(pattern=r"^[0-9]{8}$", max_length=8)
    password: SecretStr = Field(min_length=15, max_length=128)


class CustomerLoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str
    expires_at: int
    customer_id: str
    # Cross-origin SPAs cannot read a non-HttpOnly cookie on the API origin.
    # Returning this CSRF nonce lets the browser send the double-submit header
    # without exposing the session cookie.
    csrf_token: str | None = None


class AgentRunRequest(BaseModel):
    """Request payload for running the banking agent."""

    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    customer_id: str | None = Field(
        None, description="Explicit customer ID (permitted in local/development mode only)"
    )
    session_id: str | None = Field(
        None, description="Optional caller session identifier for persistence"
    )


class AgentRunResponse(BaseModel):
    """Response payload containing grounded answer and execution metadata."""

    answer: str
    customer_id: str
    rounds: int
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None
    execution_mode: str = Field(
        description="Observed execution path: azure-foundry, deterministic, or cloud-fallback"
    )
    latency_ms: float = Field(ge=0)
    tool_count: int = Field(ge=0)
    approval_requests: list[dict[str, Any]] = Field(default_factory=list)


class ServiceRequestItem(BaseModel):
    service_request_id: str
    category: str
    description: str
    status: str
    created_at: str


class ServiceRequestCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category: str = Field(..., pattern=r"^(LOAN|INSTALLMENT|FEE|GENERAL)$")
    description: str = Field(..., min_length=5, max_length=240)
    customer_id: str | None = Field(
        None, description="Optional legacy caller hint; verified token identity takes precedence"
    )


class ServiceRequestListResponse(BaseModel):
    items: list[ServiceRequestItem]


class ApprovalDecisionRequest(BaseModel):
    approved: bool


class ConversationSummary(BaseModel):
    session_id: str
    updated_at: str | None = None
    turn_count: int = 0


class ConversationTurn(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


@dataclass(frozen=True, slots=True)
class PrincipalContext:
    """Verified principal identity."""

    customer_id: str
    authenticated: bool
    claims: dict[str, Any] = field(default_factory=dict)


class AuthenticationProvider:
    """Authentication and identity verification boundary for the HTTP API."""

    def __init__(
        self,
        jwt_validator: Callable[[str], PrincipalContext] | None = None,
        customer_auth: CustomerAuth | None = None,
    ) -> None:
        """Allow a deterministic verifier to be supplied by isolated tests."""
        self._jwt_validator = jwt_validator or self._validate_entra_jwt
        self._customer_auth = customer_auth

    def customers(self) -> CustomerAuth:
        """Explicit staging-only mode; errors never expose storage or credential details."""
        if os.getenv("AEGISBANK_AUTH_MODE", "entra") not in {"students", "synthetic-password"}:
            raise HTTPException(404, "Customer password login is not enabled")
        if resolve_runtime_environment().value == "production":
            raise HTTPException(503, "Students authentication is restricted to the laboratory")
        try:
            if self._customer_auth is None:
                self._customer_auth = CustomerAuth(CosmosAuthStore())
            return self._customer_auth
        except Exception as exc:
            raise HTTPException(503, "Autenticación temporalmente no disponible") from exc

    @staticmethod
    def _validate_entra_jwt(token: str) -> PrincipalContext:
        """Verify an Entra-issued JWT and bind the customer identity to its claims.

        Cloud startup deliberately does not invent a tenant, audience, or customer
        mapping.  Missing configuration makes authenticated requests unavailable
        rather than accepting an arbitrary bearer value.
        """
        tenant_id = os.getenv("AEGISBANK_ENTRA_TENANT_ID", "").strip()
        audience = os.getenv("AEGISBANK_ENTRA_AUDIENCE", "").strip()
        customer_claim = os.getenv("AEGISBANK_ENTRA_CUSTOMER_ID_CLAIM", "customer_id").strip()
        if not tenant_id or not audience:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloud JWT verification is not configured",
            )

        try:
            import jwt
            from jwt import PyJWKClient

            issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
            # Microsoft Entra publishes tenant JWKS one level above the v2.0
            # issuer URL. Appending discovery to ``issuer`` produces a 404
            # (``.../v2.0/discovery/v2.0/keys``) in hosted runtimes.
            jwks_client = PyJWKClient(
                f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
            )
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except Exception as exc:
            logger.warning("Cloud JWT validation failed: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        customer_id = claims.get(customer_claim)
        if not isinstance(customer_id, str) or not re.fullmatch(r"CUST-\d{4}", customer_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verified token does not contain an authorized synthetic customer identity",
            )

        return PrincipalContext(
            customer_id=customer_id,
            authenticated=True,
            claims={"auth_type": "entra-jwt", "subject": claims["sub"]},
        )

    def authenticate(
        self, request: Request, request_customer_id: str | None = None
    ) -> PrincipalContext:
        """Resolve authenticated identity. Fails closed in cloud if unverified."""
        env = resolve_runtime_environment()
        mode = os.getenv("AEGISBANK_AUTH_MODE", "entra")
        if mode not in {"entra", "students", "synthetic-password"}:
            raise HTTPException(503, "Authentication mode is invalid")

        if not env.is_cloud and mode != "students":
            # Local / development mode: permits body or header for synthetic customer simulation
            effective_customer = (
                request_customer_id or request.headers.get("X-Customer-Id") or "CUST-0001"
            )
            return PrincipalContext(
                customer_id=effective_customer,
                authenticated=True,
                claims={"mode": "local-synthetic"},
            )

        # Cloud mode (staging / production): MUST have valid Bearer token
        # Never trust arbitrary customer_id from request body or X-Customer-Id alone!
        auth_header = request.headers.get("Authorization", "")
        token = (
            auth_header[7:].strip()
            if auth_header.startswith("Bearer ")
            else request.cookies.get("aegisbank_session", "")
        )
        cookie_auth = not auth_header.startswith("Bearer ") and bool(token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: valid Bearer token missing in cloud environment",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if cookie_auth and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            csrf_cookie = request.cookies.get("aegisbank_csrf", "")
            csrf_header = request.headers.get("X-CSRF-Token", "")
            if not csrf_cookie or not hmac.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(status_code=403, detail="CSRF validation failed")

        # In cloud, customer identity is bound only to verified token claims,
        # never to the request body or X-Customer-Id header.
        if mode in {"students", "synthetic-password"}:
            try:
                customer_id = self.customers().authenticate(token)
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(503, "Autenticación temporalmente no disponible") from exc
            return PrincipalContext(customer_id, True, {"auth_type": "students-session"})
        return self._jwt_validator(token)


def create_app(
    orchestrator: AgentOrchestrator | None = None,
    auth_provider: AuthenticationProvider | None = None,
) -> FastAPI:
    """Application factory for the hosted Agent HTTP API."""
    app = FastAPI(
        title="AegisBank Agent API",
        version="1.0.0",
        description="Production HTTP adapter for the AegisBank AI Agent Orchestrator",
    )
    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv("AEGISBANK_CORS_ORIGINS", "").split(",")
        if origin.strip()
    )
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    auth = auth_provider or AuthenticationProvider()
    conversation_store: ConversationStore | None = None
    if os.getenv("CONVERSATION_PERSISTENCE_ENABLED", "false").lower() == "true":
        conversation_store = ConversationStore()

    @app.exception_handler(RequestValidationError)
    async def redact_login_validation(request: Request, exc: RequestValidationError):
        # FastAPI validation errors otherwise echo rejected input (including passwords).
        if request.url.path.startswith("/api/v1/auth/"):
            return JSONResponse(
                status_code=422,
                content={"detail": "Datos de acceso no válidos"},
                headers={"Cache-Control": "no-store"},
            )
        return await request_validation_exception_handler(request, exc)

    @app.post(
        "/api/v1/auth/login",
        response_model=CustomerLoginResponse,
        response_model_exclude_none=True,
        tags=["Authentication"],
    )
    def customer_login(payload: CustomerLoginRequest, response: Response):
        response.headers["Cache-Control"] = "no-store"
        try:
            result = auth.customers().login(payload.dni, payload.password.get_secret_value())
            token = result.pop("access_token")
            csrf = secrets.token_urlsafe(32)
            response.set_cookie(
                "aegisbank_session",
                token,
                max_age=900,
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
            )
            response.set_cookie(
                "aegisbank_csrf",
                csrf,
                max_age=900,
                httponly=False,
                secure=True,
                samesite="none",
                path="/",
            )
            result["csrf_token"] = csrf
            result["token_type"] = "Cookie"
            return result
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Autenticación temporalmente no disponible") from exc

    @app.post("/api/v1/auth/logout", status_code=204, tags=["Authentication"])
    def customer_logout(request: Request):
        customers = auth.customers()
        header = request.headers.get("Authorization", "")
        token = (
            header[7:].strip()
            if header.startswith("Bearer ")
            else request.cookies.get("aegisbank_session", "")
        )
        if not token:
            raise HTTPException(401, "Sesión no válida")
        if not header.startswith("Bearer "):
            csrf_cookie = request.cookies.get("aegisbank_csrf", "")
            csrf_header = request.headers.get("X-CSRF-Token", "")
            if not csrf_cookie or not hmac.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(403, "CSRF validation failed")
        try:
            customers.logout(token)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Autenticación temporalmente no disponible") from exc
        result = Response(status_code=204, headers={"Cache-Control": "no-store"})
        result.delete_cookie("aegisbank_session", path="/")
        result.delete_cookie("aegisbank_csrf", path="/")
        return result

    @app.get("/api/v1/auth/me", tags=["Authentication"])
    def customer_me(request: Request, response: Response) -> dict[str, str]:
        response.headers["Cache-Control"] = "no-store"
        header = request.headers.get("Authorization", "")
        token = (
            header[7:].strip()
            if header.startswith("Bearer ")
            else request.cookies.get("aegisbank_session", "")
        )
        if not token:
            raise HTTPException(401, "Sesión no válida", headers={"WWW-Authenticate": "Bearer"})
        customer_id = auth.customers().authenticate(token)
        csrf = request.cookies.get("aegisbank_csrf", "")
        if not csrf and not header.startswith("Bearer "):
            csrf = secrets.token_urlsafe(32)
            response.set_cookie(
                "aegisbank_csrf",
                csrf,
                max_age=900,
                httponly=False,
                secure=True,
                samesite="none",
                path="/",
            )
        result = {"customer_id": customer_id}
        if csrf:
            result["csrf_token"] = csrf
        return result

    @app.get(
        "/api/v1/conversations",
        response_model=list[ConversationSummary],
        tags=["Conversations"],
    )
    def list_conversations(request: Request) -> list[ConversationSummary]:
        if conversation_store is None:
            raise HTTPException(503, "Conversation history is not configured")
        principal = auth.authenticate(request)
        try:
            return [
                ConversationSummary(**item)
                for item in conversation_store.list_sessions(principal.customer_id)
            ]
        except Exception as exc:
            logger.error("Conversation listing failed: %s", type(exc).__name__)
            return []

    @app.get(
        "/api/v1/conversations/{session_id}",
        response_model=list[ConversationTurn],
        tags=["Conversations"],
    )
    def get_conversation(session_id: str, request: Request) -> list[ConversationTurn]:
        if conversation_store is None:
            raise HTTPException(503, "Conversation history is not configured")
        principal = auth.authenticate(request)
        if len(session_id) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise HTTPException(400, "Invalid conversation identifier")
        try:
            return [
                ConversationTurn(**item)
                for item in conversation_store.get_session(principal.customer_id, session_id)
            ]
        except Exception as exc:
            logger.error("Conversation retrieval failed: %s", type(exc).__name__)
            return []

    orchestrator_init_error: RuntimeError | None = None
    if orchestrator is not None:
        agent_orchestrator = orchestrator
    else:
        try:
            agent_orchestrator = AgentOrchestrator()
        except RuntimeError as exc:
            # Keep liveness available while an optional cloud model provider is unavailable.
            logger.error("Agent orchestrator initialization failed: %s", exc)
            agent_orchestrator = None
            orchestrator_init_error = exc

    @app.get("/health/live", tags=["Health"])
    def liveness() -> dict[str, str]:
        """Liveness probe: verifies process is alive without querying external dependencies."""
        return {"status": "alive"}

    @app.get("/health/ready", tags=["Health"])
    def readiness() -> dict[str, Any]:
        """Readiness probe: validates configuration and required runtime dependencies."""
        env = resolve_runtime_environment()
        try:
            validate_runtime_configuration(env)
            mode = os.getenv("AEGISBANK_AUTH_MODE", "entra")
            if mode not in {"entra", "students", "synthetic-password"}:
                raise EnvironmentSelectionError("Authentication mode is invalid")
            if mode in {"students", "synthetic-password"}:
                try:
                    auth.customers().store.ready()
                except Exception as exc:
                    raise EnvironmentSelectionError(
                        "Authentication storage is unavailable"
                    ) from exc
            return {"status": "ready", "environment": env.value}
        except EnvironmentSelectionError as exc:
            logger.error("Readiness check failed due to invalid configuration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unready: runtime configuration invalid or incomplete",
            ) from exc

    @app.get(
        "/api/v1/me/service-requests",
        response_model=ServiceRequestListResponse,
        tags=["Service requests"],
    )
    def list_my_service_requests(
        request: Request,
        response: Response,
    ) -> ServiceRequestListResponse:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        principal = auth.authenticate(request)
        core_url = os.getenv("AEGISBANK_CORE_BANKING_URL") or os.getenv("CORE_BANKING_URL")
        if not core_url:
            raise HTTPException(
                status_code=503,
                detail="Core Banking service is not configured",
            )
        target = f"{core_url.rstrip('/')}/api/v1/service-requests/customer/{principal.customer_id}"
        try:
            request_to_core = urllib.request.Request(target, headers={"Accept": "application/json"})
            with urllib.request.urlopen(  # nosec B310 - configured service URL
                request_to_core, timeout=10.0
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return ServiceRequestListResponse(items=[])
            raise HTTPException(
                status_code=503,
                detail="Core Banking service temporarily unavailable",
            ) from exc
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=503,
                detail="Core Banking service temporarily unavailable",
            ) from exc
        if not isinstance(payload, list):
            raise HTTPException(
                status_code=503,
                detail="Core Banking returned an invalid request feed",
            )
        return ServiceRequestListResponse(
            items=[ServiceRequestItem(**item) for item in payload if isinstance(item, dict)]
        )

    @app.post(
        "/api/v1/service-requests",
        response_model=ServiceRequestItem,
        status_code=status.HTTP_201_CREATED,
        tags=["Service requests"],
    )
    def create_service_request(
        payload: ServiceRequestCreateRequest,
        request: Request,
        response: Response,
    ) -> ServiceRequestItem:
        """Create a customer-owned request through Core Banking."""
        response.headers["Cache-Control"] = "no-store"
        principal = auth.authenticate(request)
        core_url = os.getenv("AEGISBANK_CORE_BANKING_URL") or os.getenv("CORE_BANKING_URL")
        if not core_url:
            raise HTTPException(status_code=503, detail="Core Banking service is not configured")
        body = json.dumps(
            {
                "customer_id": principal.customer_id,
                "category": payload.category,
                "description": payload.description.strip(),
            }
        ).encode("utf-8")
        target = f"{core_url.rstrip('/')}/api/v1/service-requests"
        try:
            request_to_core = urllib.request.Request(
                target,
                data=body,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request_to_core, timeout=10.0) as response:  # nosec B310
                result = json.loads(response.read().decode("utf-8"))
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise HTTPException(
                status_code=503, detail="Core Banking service temporarily unavailable"
            ) from exc
        if not isinstance(result, dict):
            raise HTTPException(status_code=503, detail="Core Banking returned an invalid request")
        return ServiceRequestItem(**result)

    @app.post("/api/v1/approvals/{approval_id}", tags=["Agent approvals"])
    def decide_approval(
        approval_id: str,
        payload: ApprovalDecisionRequest,
        request: Request,
    ) -> dict[str, Any]:
        """Approve/reject a pending chat WRITE proposal and execute only after approval."""
        if agent_orchestrator is None:
            raise HTTPException(status_code=503, detail="Agent model provider is not configured")
        principal = auth.authenticate(request)
        manager = agent_orchestrator.hitl_manager
        try:
            current = manager.get_request(approval_id)
            if current.synthetic_customer_id != principal.customer_id:
                raise HTTPException(status_code=404, detail="Approval request not found")
            if not payload.approved:
                result = manager.reject(approval_id, principal.customer_id, "Rechazado por el cliente")
                return {"approval": result.as_dict(), "executed": False}
            approved = manager.approve(approval_id, principal.customer_id)
            tool_result = agent_orchestrator.registry.execute(
                approved.tool_name,
                approved.normalized_arguments,
                AgentContext(session_customer_id=principal.customer_id),
            )
            if not tool_result.success:
                raise HTTPException(status_code=503, detail="Core Banking service temporarily unavailable")
            executed = manager.verify_and_mark_executed(
                approval_id,
                principal.customer_id,
                approved.normalized_arguments,
                tool_result.data or {},
            )
            return {"approval": executed.as_dict(), "executed": True}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Approval request not found") from exc

    @app.post("/api/v1/agent/run", response_model=AgentRunResponse, tags=["Agent"])
    def run_agent(
        payload: AgentRunRequest,
        request: Request,
    ) -> AgentRunResponse:
        """Execute a natural language banking query through the AgentOrchestrator."""
        if agent_orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent model provider is not configured",
            ) from orchestrator_init_error
        principal = auth.authenticate(request, request_customer_id=payload.customer_id)

        started_at = time.perf_counter()
        try:
            result: AgentExecutionResult = agent_orchestrator.run(
                user_message=payload.query,
                customer_id=principal.customer_id,
                session_id=payload.session_id,
            )
            if (
                resolve_runtime_environment() is RuntimeEnvironment.PRODUCTION
                and isinstance(result.error, str)
                and result.error
            ):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI provider unavailable; production fallback disabled",
                )
            effective_session_id = payload.session_id or f"session-{principal.customer_id}"
            if result.error and "Azure AI Foundry" in result.answer:
                execution_mode = "cloud-fallback"
            elif result.rounds > 0:
                execution_mode = "azure-foundry"
            else:
                execution_mode = "deterministic"
            if conversation_store is not None:
                try:
                    conversation_store.append_turn(
                        customer_id=principal.customer_id,
                        session_id=effective_session_id,
                        role="user",
                        content=payload.query,
                    )
                    conversation_store.append_turn(
                        customer_id=principal.customer_id,
                        session_id=effective_session_id,
                        role="assistant",
                        content=result.answer,
                        metadata={
                            "execution_mode": execution_mode,
                            "rounds": result.rounds,
                            "tool_count": len(result.tool_calls),
                            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
                        },
                    )
                except Exception as persistence_error:
                    # A Cosmos outage must not turn an otherwise valid banking
                    # answer into a misleading agent 500. Retrieval remains
                    # explicitly 503, while this request returns the answer
                    # and records a redacted operational signal for repair.
                    logger.error(
                        "Conversation persistence failed; answer returned without history: %s",
                        type(persistence_error).__name__,
                    )
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            return AgentRunResponse(
                answer=result.answer,
                customer_id=result.customer_id,
                rounds=result.rounds,
                tool_calls=[
                    {
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                    }
                    for tc in result.tool_calls
                ],
                session_id=effective_session_id,
                execution_mode=execution_mode,
                latency_ms=latency_ms,
                tool_count=len(result.tool_calls),
                approval_requests=[req.as_dict() for req in result.approval_requests],
            )
        except Exception as exc:
            logger.error(
                "Agent execution failed; returning safe degraded response: %s",
                type(exc).__name__,
            )
            if resolve_runtime_environment() is RuntimeEnvironment.PRODUCTION:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI provider unavailable; production fallback disabled",
                ) from exc
            # Keep the HTTP contract usable during transient Foundry/Cosmos
            # failures. Never fabricate banking data or expose provider errors;
            # the explicit mode lets the UI distinguish this from an AI answer.
            effective_session_id = payload.session_id or f"session-{principal.customer_id}"
            return AgentRunResponse(
                answer=(
                    "No pudimos completar la consulta bancaria en este momento. "
                    "Tus datos no se modificaron; vuelve a intentarlo en unos segundos."
                ),
                customer_id=principal.customer_id,
                rounds=0,
                tool_calls=[],
                session_id=effective_session_id,
                execution_mode="cloud-fallback",
                latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
                tool_count=0,
            )

    return app


app = create_app()
