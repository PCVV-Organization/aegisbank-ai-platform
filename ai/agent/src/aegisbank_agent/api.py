"""Hosted HTTP API adapter for AegisBank AgentOrchestrator.

Provides production HTTP endpoints (/health/live, /health/ready, /api/v1/agent/run)
without replacing the existing CLI or MCP stdio interfaces.
Enforces an explicit authentication boundary in cloud environments.
"""

from __future__ import annotations

import hmac
import logging
import os
import re
import secrets
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from .agent import AgentExecutionResult, AgentOrchestrator
from .configuration.environment import (
    EnvironmentSelectionError,
    resolve_runtime_environment,
    validate_runtime_configuration,
)
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
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
        )

    auth = auth_provider or AuthenticationProvider()

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

        try:
            result: AgentExecutionResult = agent_orchestrator.run(
                user_message=payload.query,
                customer_id=principal.customer_id,
                session_id=payload.session_id,
            )
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
                session_id=payload.session_id,
            )
        except Exception as exc:
            logger.error("Agent execution failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent execution encountered an unhandled internal error",
            ) from exc

    return app


app = create_app()
