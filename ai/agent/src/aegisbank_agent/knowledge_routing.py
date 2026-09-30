"""Deterministic policy for grounding banking knowledge questions before generation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

_LOAN_STATUS_KNOWLEDGE_PATTERNS = (
    r"\bque\s+(?:es|significa)\s+(?:el\s+)?(?:estado\s+)?delinquent\b",
    r"\bdefinicion\s+de\s+(?:estado\s+)?delinquent\b",
    r"\bque\s+(?:es|significa)\s+la\s+morosidad\b",
    r"\bque\s+(?:es|significa)\s+un\s+prestamo\s+moroso\b",
    r"\bque\s+estados?\s+(?:tenemos|puede(?:n)?\s+tener|existen)\b",
    r"\bestados?\s+(?:de\s+)?(?:un\s+)?prestamo\b",
)
_POLICY_TERMS = (
    "politica",
    "requisito",
    "comision",
    "tasa",
    "interes",
    "plazo",
    "condicion",
    "producto",
    "credito",
)
_PRODUCT_ANCHORS = ("vehicular", "hipotecario", "personal", "negocio", "capital de trabajo")
_STOPWORDS = {"cual", "cuales", "para", "los", "las", "del", "una", "un", "que"}
_ACCOUNT_PATTERNS = (
    r"\bmis\s+prestamos?\b",
    r"\bmi\s+prestamo\b",
    r"\bmis\s+cuotas?\b",
    r"\bmi\s+saldo\b",
    r"\bcuanto\s+debo\b",
    r"\bproxima\s+cuota\b",
    r"\bdetalle\s+de\s+mi\s+prestamo\b",
    r"\bque\s+(?:tengo|poseo)\b",
    r"\bprestamos?\s+(?:que\s+)?tengo\b",
    r"\bcu[aá]l\s+es\s+el\s+pr[eé]stamo\b",
    r"\bpr[eé]stamo\s+con\s+m[aá]s\s+saldo\b",
    r"\bm[aá]s\s+saldo\s+pendiente\b",
    r"\bsaldo\s+pendiente\s+que\s+tengo\b",
    r"\bfechas?\s+de\s+pago\b",
    r"\bdeudas?\s+(?:que\s+)?tengo\b",
    r"\bqu[eé]\s+(?:pr[eé]stamos?|cuotas?|deudas?)\s+tengo\b",
)
_LAST_LOAN_PATTERNS = (
    r"\b(?:ultimo|ultima)\s+prestamo\b",
    r"\bprestamo\s+(?:anterior|ultimo|previo)\b",
    r"\bel\s+anterior\b",
    r"\bde\s+ese\s+prestamo\b",
    r"\bde\s+este\s+prestamo\b",
    r"\bde\s+ese\b",
    r"\bpor\s+el\s+que\s+(?:te\s+)?(?:consulte|pregunte)\b",
    r"\bporque\s+el\s+que\s+(?:te\s+)?(?:consulte|pregunte)\b",
    r"\bque\s+(?:te\s+)?(?:consulte|pregunte)\s+(?:antes|recien)\b",
    r"\bque\s+prestamo\s+(?:te\s+)?(?:consulte|pregunte)\b",
    r"\bque\s+prestamo\s+(?:fue|era)\b",
)

_LOAN_ID_REGEX = re.compile(r"\bLOAN-[0-9]{4}\b", re.IGNORECASE)
_CUSTOMER_ID_REGEX = re.compile(r"\bCUST-[0-9]{4}\b", re.IGNORECASE)
_GREETING_TERMS = ("hola", "buenos dias", "buenas tardes", "buenas noches", "saludos", "que tal")
_OWNERSHIP_PATTERNS = (
    r"\bes\s+m[ií]o\b",
    r"\bes\s+de\s+otro\b",
    r"\bde\s+qui[eé]n\s+es\b",
    r"\ba\s+qui[eé]n\s+pertenece\b",
    r"\bme\s+pertenece\b",
    r"\bes\s+mi\s+pr[eé]stamo\b",
    r"\bes\s+de\s+otro\s+usuario\b",
    r"\bes\s+de\s+otro\s+cliente\b",
    r"\bpertenece\s+a\s+m[ií]\b",
)


_COMPARATIVE_LOAN_PATTERNS = (
    r"\bmas\s+saldo\b",
    r"\bmayor\s+saldo\b",
    r"\bmas\s+saldo\s+pendiente\b",
    r"\bmayor\s+saldo\s+pendiente\b",
    r"\bmas\s+deuda\b",
    r"\bmayor\s+deuda\b",
    r"\bprestamo\s+con\s+mas\s+saldo\b",
    r"\bprestamo\s+con\s+mayor\s+saldo\b",
    r"\btiene\s+mas\s+saldo\b",
    r"\btiene\s+mayor\s+saldo\b",
)
_PAYMENT_DATE_PATTERNS = (
    r"\bfechas?\s+de\s+pago\b",
    r"\bfecha\s+de\s+vencimiento\b",
    r"\bfechas?\s+de\s+vencimiento\b",
    r"\bcuando\s+(?:debo\s+|tengo\s+que\s+)?pagar(?:los)?\b",
    r"\bcuando\s+vence\b",
    r"\b(?:proxima|siguiente)\s+cuota\b",
    r"\bcuota\s+pendiente\b",
    r"\bcuota(?:\s+[a-z0-9]+){0,2}\s+pendiente\b",
    r"\bvencimientos?\b",
)
_PLACEHOLDER_REGEX = re.compile(
    r"\[(?:Nombre|Fecha|Monto|Breve\s+pausa|Pide\s+a|Detalle|Cliente|Pr[eé]stamo|ID|Tasa|Banco|Usuario|Cuota|Saldo|Numero|Número)[^\]]*\]|"
    r"\[[A-Za-zÁÉÍÓÚáéíóúñÑ0-9\s_\-]{3,60}\]",
    re.IGNORECASE,
)
_FAKE_TOOL_CLAIM_PATTERNS = (
    r"\bhe\s+encontrado\s+(?:los\s+detalles|la\s+informacion|tus\s+prestamos|tus\s+datos)\b",
    r"\bhe\s+consultado\s+(?:tus\s+prestamos|tus\s+cuentas|el\s+sistema|tus\s+datos)\b",
    r"\bacabo\s+de\s+(?:revisar|verificar|consultar)\b",
    r"\brevisando\s+tus\s+datos\b",
    r"\bsegun\s+he\s+consultado\b",
)
_PROCESS_HALLUCINATION_PATTERNS = (
    r"\[(?:breve\s+)?pausa[^\]]*\]",
    r"\b(?:un\s+momento|dame\s+un\s+momento|espera\s+un\s+momento)\s+mientras\s+(?:realizo|consulto|verifico)\b",
    r"\b(?:realizando|verificando)\s+la\s+consulta\b",
    r"\bbreve\s+pausa\s+mientras\b",
)


def _normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


def extract_loan_id(query: str) -> str | None:
    """Return a canonical ``LOAN-XXXX`` identifier or ``None`` if not found.

    Reuses the canonical 4-digit format used by Core Banking (``LOAN-[0-9]{4}``).
    The match is case-insensitive and returns the upper-cased string.
    """
    match = _LOAN_ID_REGEX.search(query)
    if match is None:
        return None
    return match.group(0).upper()


def extract_customer_ids(query: str) -> list[str]:
    """Return all canonical ``CUST-XXXX`` customer identifiers found in query."""
    return [match.upper() for match in _CUSTOMER_ID_REGEX.findall(query)]


def is_cross_customer_attempt(query: str, session_customer_id: str) -> bool:
    """Return True if query explicitly claims or requests access to another customer ID."""
    mentioned = extract_customer_ids(query)
    if not mentioned:
        return False
    normalized_session = session_customer_id.strip().upper()
    return any(cid != normalized_session for cid in mentioned)


def asks_loan_ownership(query: str) -> bool:
    """Detect if user asks whether a loan belongs to them or someone else."""
    normalized = _normalize(query)
    return any(re.search(pat, normalized) for pat in _OWNERSHIP_PATTERNS)


def is_last_loan_reference(query: str) -> bool:
    """Identify a safe, structured reference to the last consulted loan."""
    normalized = _normalize(query)
    return any(re.search(pattern, normalized) for pattern in _LAST_LOAN_PATTERNS)


def detect_loan_details_request(query: str) -> dict[str, Any]:
    """Classify a loan-detail intent."""
    normalized = _normalize(query)
    loan_id = extract_loan_id(query)
    has_detail_trigger = any(
        trigger in normalized
        for trigger in (
            "detalle",
            "saldo",
            "monto",
            "estado",
            "info",
            "informacion",
            "mostrar",
            "muestrame",
        )
    )
    has_loan_word = "prestamo" in normalized or "credito" in normalized
    asks_for_installment = "cuota" in normalized or "vencimiento" in normalized
    is_account_request = (has_detail_trigger or has_loan_word or loan_id is not None) and (
        loan_id is not None or not requires_authorized_knowledge(query)
    )
    return {
        "loan_id": loan_id,
        "needs_loan_list_first": ((has_detail_trigger or has_loan_word) and loan_id is None),
        "is_account_request": is_account_request,
        "asks_for_installment": asks_for_installment,
    }


def is_greeting(query: str) -> bool:
    """Return True for short social greetings."""
    normalized = _normalize(query).strip()
    if not normalized:
        return False
    if len(normalized.split()) > 6:
        return False
    banned_tokens = ("prestamo", "reclamo", "loan-", "puedes hacer", "credito")
    if any(token in normalized for token in banned_tokens):
        return False
    return any(normalized.startswith(term) or normalized == term for term in _GREETING_TERMS)


def is_capability_query(query: str) -> bool:
    """Return True when the user asks about what the agent can do."""
    normalized = _normalize(query)
    triggers = (
        "que puedes hacer",
        "que puedes",
        "que sabes hacer",
        "que hace",
        "en que me puedes ayudar",
        "como me puedes ayudar",
        "cuales son tus funciones",
        "cuales son sus funciones",
    )
    return any(trigger in normalized for trigger in triggers)


def is_comparative_loan_query(query: str) -> bool:
    """Return True when user asks to compare loans (e.g. highest balance, most debt)."""
    normalized = _normalize(query)
    return any(re.search(pat, normalized) for pat in _COMPARATIVE_LOAN_PATTERNS)


def asks_my_loan_statuses(query: str) -> bool:
    """Return True when an authenticated user asks for their loans' statuses."""
    normalized = _normalize(query)
    return (
        extract_loan_id(query) is None
        and "estado" in normalized
        and ("prestamo" in normalized or "credito" in normalized)
        and any(token in normalized for token in ("mi ", "mis ", "tengo"))
    )


def asks_for_payment_dates(query: str) -> bool:
    """Return True for a read-only next-installment or payment-schedule intent.

    This is a bounded semantic family, not a list of one-off sentences.  It
    deliberately requires a due-date, schedule, or interrogative payment signal;
    an imperative such as ``paga LOAN-0001`` remains outside this read intent.
    """
    normalized = _normalize(query)
    return any(re.search(pat, normalized) for pat in _PAYMENT_DATE_PATTERNS)


def has_placeholder_leak(text: str) -> bool:
    """Detect template placeholders like [Nombre del Préstamo] or [Fecha de Pago]."""
    return bool(_PLACEHOLDER_REGEX.search(text))


def has_fake_tool_claim(text: str) -> bool:
    """Detect claims of having retrieved information without underlying tool execution."""
    normalized = _normalize(text)
    return any(re.search(pat, normalized) for pat in _FAKE_TOOL_CLAIM_PATTERNS)


def has_process_hallucination(text: str) -> bool:
    """Detect simulated internal process or fake waiting language."""
    normalized = _normalize(text)
    return any(re.search(pat, normalized) for pat in _PROCESS_HALLUCINATION_PATTERNS)


_WRITE_ACTION_PATTERNS = (
    r"\b(?:crea|registra|presenta|abre|genera)\s+(?:un\s+|una\s+)?"
    r"(?:reclamo|solicitud|queja|ticket|caso|impugnacion|reprogramacion)\b",
    r"\b(?:registrar|crear|ingresar|presentar|generar|iniciar|abrir|hacer|formular|meter|solicitar|poner)\s+"
    r"(?:un\s+|una\s+)?(?:reclamo|solicitud|queja|ticket|caso|impugnacion|reprogramacion)\b",
    r"\b(?:reclamo|solicitud|queja|impugnacion)\s+(?:nuevo|nueva|urgente)\b",
    r"\bquiero\s+(?:reclamar|quejarme|solicitar|impugnar|hacer\s+un\s+reclamo|presentar\s+un\s+reclamo|poner\s+un\s+reclamo)\b",
    r"\bdeseo\s+(?:reclamar|impugnar|presentar\s+un\s+reclamo|registrar\s+un\s+reclamo|poner\s+un\s+reclamo)\b",
    r"\b(?:registrar|crear|ingresar|solicitar)\s+(?:reclamo|solicitud|reprogramacion)\b",
    r"\btengo\s+(?:un\s+|una\s+)?(?:reclamo|queja|inconformidad)\b",
    r"\bcreate_service_request\b",
)


def requires_write_action(query: str) -> bool:
    """Return True if user explicitly requests to create or register a service request/claim."""
    normalized = _normalize(query)
    if any(
        term in normalized
        for term in (
            "procedimiento",
            "requisito",
            "requisitos",
            "normativa",
            "como presentar",
            "como registrar",
            "como crear",
            "como formular",
        )
    ):
        return False
    return any(re.search(pattern, normalized) for pattern in _WRITE_ACTION_PATTERNS)


def requires_authorized_knowledge(query: str) -> bool:
    """Return true only for factual banking policy/product questions."""
    if requires_write_action(query):
        return False
    normalized = _normalize(query)
    return any(term in normalized for term in _POLICY_TERMS) or any(
        re.search(pattern, normalized) for pattern in _LOAN_STATUS_KNOWLEDGE_PATTERNS
    )


def requires_account_data(query: str) -> bool:
    """Identify questions requiring authenticated Core Banking data."""
    if extract_loan_id(query) is not None:
        return True
    if is_last_loan_reference(query):
        return True
    if is_comparative_loan_query(query):
        return True
    normalized = _normalize(query)
    return any(re.search(pattern, normalized) for pattern in _ACCOUNT_PATTERNS)


def account_tool_allowlist(query: str) -> list[str]:
    """Return the smallest READ tool set for an authenticated account query."""
    normalized = _normalize(query)
    loan_id = extract_loan_id(query)
    if is_last_loan_reference(query):
        return ["get_loan_details"]
    if is_comparative_loan_query(query):
        comp_tools = ["get_my_loans"]
        if asks_for_payment_dates(query):
            comp_tools.append("get_next_installment")
        return comp_tools
    tools: list[str] = []

    if loan_id is not None:
        # A due-date/installment question is more specific than the generic
        # presence of a loan identifier.  Force only its read tool so the agent
        # cannot substitute total outstanding balance for a scheduled installment.
        if asks_for_payment_dates(query):
            return ["get_next_installment"]
        return ["get_loan_details"]

    needs_loan_list = (
        "mis prestamos" in normalized
        or "mi prestamo" in normalized
        or "prestamo" in normalized
        or "prestamos" in normalized
        or "que tengo" in normalized
        or "saldo pendiente" in normalized
        or "tengo" in normalized
    )
    if needs_loan_list:
        tools.append("get_my_loans")
    if (
        "proxima cuota" in normalized
        or "cuanto debo" in normalized
        or "mis cuotas" in normalized
        or "fechas de pago" in normalized
        or "fecha de pago" in normalized
        or "fechas" in normalized
        or "cuotas" in normalized
    ):
        if "get_my_loans" not in tools:
            tools.append("get_my_loans")
        tools.append("get_next_installment")
    if "detalle" in normalized or "saldo" in normalized:
        if "get_my_loans" not in tools:
            tools.append("get_my_loans")
        tools.append("get_loan_details")
    if "prestamo" in normalized and not tools:
        tools.append("get_my_loans")
    return tools or ["get_my_loans"]


def classify_service_inquiry(query: str) -> str:
    """Classify service request/claims inquiries into DOMAIN_SCHEMA, RAG, or CLARIFICATION."""
    normalized = _normalize(query)
    claim_terms = ("reclamo", "reclamacion", "queja", "solicitud de servicio", "solicitud")
    if not any(term in normalized for term in claim_terms):
        return "OTHER"

    schema_triggers = (
        "que campos",
        "cuales son los campos",
        "que datos necesito",
        "que datos se requieren",
        "datos obligatorios",
        "campos obligatorios",
        "que categorias",
        "cuales son las categorias",
        "tipos de solicitud",
        "tipos de reclamo",
        "categorias de reclamo",
        "categorias soportadas",
    )
    if any(trigger in normalized for trigger in schema_triggers):
        return "DOMAIN_SCHEMA"

    policy_triggers = (
        "politica de reclamo",
        "politica de atencion",
        "procedimiento de reclamo",
        "procedimiento y requisitos",
        "procedimiento",
        "plazos legales",
        "plazo de respuesta",
        "normativa de reclamos",
    )
    if any(trigger in normalized for trigger in policy_triggers):
        return "RAG"

    ambiguous_triggers = (
        "para que mi reclamo tenga efecto",
        "para que mi reclamo proceda",
        "para que proceda mi reclamo",
        "para que sea valido mi reclamo",
        "que requiero para que mi reclamo",
        "que requiero para mi reclamo",
        "que se requiere para un reclamo",
        "requisitos para mi reclamo",
        "requisitos de un reclamo",
    )
    if any(trigger in normalized for trigger in ambiguous_triggers):
        return "CLARIFICATION"

    if (
        "requiero" in normalized or "requisito" in normalized or "se requiere" in normalized
    ) and any(term in normalized for term in ("reclamo", "solicitud")):
        return "CLARIFICATION"

    return "OTHER"


def has_sufficient_evidence(query: str, data: Any) -> bool:
    """Reject generic hits when a product-specific fact was not retrieved."""
    hits = data.get("hits", []) if isinstance(data, dict) else []
    if not hits:
        return False
    corpus_text = _normalize(" ".join(str(hit) for hit in hits))
    normalized_query = _normalize(query)
    for anchor in _PRODUCT_ANCHORS:
        if anchor in normalized_query and anchor not in corpus_text:
            return False
    terms = {
        token
        for token in re.findall(r"[a-z0-9]+", normalized_query)
        if len(token) > 3 and token not in _STOPWORDS
    }
    return len(terms.intersection(set(re.findall(r"[a-z0-9]+", corpus_text)))) >= 2


@dataclass(frozen=True)
class KnowledgeRoutingDecision:
    required: bool
    sufficient: bool
    result: Any = None


def resolve_minimal_tool_allowlist(query: str, available_tools: list[str]) -> list[str]:
    """Return the minimal tool set required for the active user intent (Least Agency).

    Enforces defense-in-depth:
    - GREETING / CAPABILITY: zero tools exposed.
    - WRITE_ACTION: exposes create_service_request + referenced account tools.
    - ACCOUNT_READ: exposes strictly account allowlist (no WRITE tools).
    - KNOWLEDGE: exposes strictly search_knowledge (no account/write tools).
    - OTHER: fallback to all available tools.
    """
    if is_greeting(query) or is_capability_query(query):
        return []

    write_required = requires_write_action(query)
    account_required = requires_account_data(query)
    knowledge_required = requires_authorized_knowledge(query)

    resolved: set[str] = set()

    if write_required:
        if "create_service_request" in available_tools:
            resolved.add("create_service_request")
        if account_required:
            for t in account_tool_allowlist(query):
                if t in available_tools:
                    resolved.add(t)
        return [t for t in available_tools if t in resolved]

    if account_required:
        account_tools = set(account_tool_allowlist(query))
        return [t for t in available_tools if t in account_tools]

    if knowledge_required:
        return [t for t in available_tools if t == "search_knowledge"]

    return list(available_tools)


def redact_foreign_customer_ids(
    text: str, session_customer_id: str, replacement: str = "[CLIENTE-REDACTADO]"
) -> str:
    """Replace canonical customer IDs belonging to other customers with a sanitized token."""
    normalized_session = session_customer_id.strip().upper()

    def _repl(match: re.Match[str]) -> str:
        cid = match.group(0).upper()
        return cid if cid == normalized_session else replacement

    return _CUSTOMER_ID_REGEX.sub(_repl, text)
