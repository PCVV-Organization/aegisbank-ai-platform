"""Unit tests for the post-generation I_4 Customer IDOR interceptor and output guard."""

from __future__ import annotations

from aegisbank_agent.knowledge_routing import (
    extract_customer_ids,
    is_cross_customer_attempt,
    redact_foreign_customer_ids,
)


def test_output_guard_7_canonical_scenarios() -> None:
    """Evaluate all 7 canonical scenarios for the I_4 output interceptor."""
    session_customer = "CUST-0001"
    scenarios = [
        # Scenario 1: Unauthorized disclosure attempt (Foreign customer ID leaked in answer)
        {
            "name": "unauthorized_disclosure",
            "text": "El cliente CUST-0002 tiene un préstamo activo por 15000 PEN.",
            "expected_foreign_detected": True,
            "category": "POSITIVE",  # Foreign ID present
        },
        # Scenario 2: Clean explanation (No customer IDs)
        {
            "name": "clean_explanation",
            "text": (
                "Para acceder a un crédito vehicular debes presentar DNI y sustento de ingresos."
            ),
            "expected_foreign_detected": False,
            "category": "NEGATIVE",  # No foreign ID
        },
        # Scenario 3: Refusal explanation (Refusal without foreign customer IDs)
        {
            "name": "refusal_explanation",
            "text": "No tengo autorización para consultar datos fuera de tu sesión.",
            "expected_foreign_detected": False,
            "category": "NEGATIVE",  # No foreign ID
        },
        # Scenario 4: Policy example with foreign customer ID
        {
            "name": "policy_with_foreign_id",
            "text": "Ejemplo: si CUST-0003 solicita un duplicado, se requiere DNI.",
            "expected_foreign_detected": True,
            "category": "POSITIVE",  # Foreign ID present
        },
        # Scenario 5: Own customer ID mention (Authenticated session customer)
        {
            "name": "own_customer_id",
            "text": "Estimado cliente CUST-0001, tu préstamo LOAN-0001 se encuentra al día.",
            "expected_foreign_detected": False,
            "category": "NEGATIVE",  # Own ID, not foreign
        },
        # Scenario 6: Malformed customer tokens (Not canonical CUST-XXXX)
        {
            "name": "malformed_tokens",
            "text": "Referencias del sistema: CUSTOMER-0002, CUST_0002, CUST-12345.",
            "expected_foreign_detected": False,
            "category": "NEGATIVE",  # Malformed, no canonical foreign ID
        },
        # Scenario 7: Mixed customer IDs (Own ID + foreign customer ID)
        {
            "name": "mixed_customer_ids",
            "text": "Sesión de CUST-0001. Transferencia vinculada a cuenta de CUST-0002.",
            "expected_foreign_detected": True,
            "category": "POSITIVE",  # Foreign ID present
        },
    ]

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for s in scenarios:
        text = str(s["text"])
        expected = bool(s["expected_foreign_detected"])
        actual = is_cross_customer_attempt(text, session_customer)

        assert actual == expected, (
            f"Scenario '{s['name']}' failed: expected detection={expected}, got {actual}"
        )

        if s["category"] == "POSITIVE":
            if actual:
                tp += 1
            else:
                fn += 1
        else:
            if actual:
                fp += 1
            else:
                tn += 1

    # Confusion matrix calculations
    total_positives = tp + fn
    total_negatives = tn + fp
    fpr = fp / total_negatives if total_negatives > 0 else 0.0
    fnr = fn / total_positives if total_positives > 0 else 0.0
    leakage_rate = fn / total_positives if total_positives > 0 else 0.0
    benign_pass_rate = tn / total_negatives if total_negatives > 0 else 1.0

    # Deterministic invariants verification
    assert tp == 3, f"Expected 3 true positives, got {tp}"
    assert tn == 4, f"Expected 4 true negatives, got {tn}"
    assert fp == 0, f"Expected 0 false positives, got {fp}"
    assert fn == 0, f"Expected 0 false negatives, got {fn}"
    assert fpr == 0.0, f"Expected FPR=0.0, got {fpr}"
    assert fnr == 0.0, f"Expected FNR=0.0, got {fnr}"
    assert leakage_rate == 0.0, f"Expected leakage_rate=0.0, got {leakage_rate}"
    assert benign_pass_rate == 1.0, f"Expected benign_pass_rate=1.0, got {benign_pass_rate}"


def test_extract_customer_ids_canonical_format() -> None:
    """extract_customer_ids must extract canonical CUST-XXXX tokens case-insensitively."""
    text = "IDs: cust-0001, CUST-0002, Cust-0003, invalid: CUST-1, CUST-ABC, CUST_0004"
    ids = extract_customer_ids(text)
    assert ids == ["CUST-0001", "CUST-0002", "CUST-0003"]


def test_redact_foreign_customer_ids() -> None:
    """redact_foreign_customer_ids must sanitize other customer IDs and preserve session ID."""
    session_customer = "CUST-0001"
    text = "El cliente CUST-0001 consultó datos de CUST-0002 y CUST-0003 en el sistema."
    redacted = redact_foreign_customer_ids(text, session_customer, "[REDACTADO]")
    assert "CUST-0001" in redacted
    assert "CUST-0002" not in redacted
    assert "CUST-0003" not in redacted
    assert redacted == (
        "El cliente CUST-0001 consultó datos de [REDACTADO] y [REDACTADO] en el sistema."
    )


def test_output_guard_tp_foreign_customer_disclosure() -> None:
    """Foreign customer ID in generated output must be detected as cross-customer attempt (TP)."""
    session_customer = "CUST-0001"
    disclosures = [
        "El préstamo LOAN-0002 pertenece al cliente CUST-0002 con saldo de 12000 PEN.",
        "Datos de cuenta de CUST-9999 recuperados exitosamente.",
        "SBS auditoria: el titular es cust-0005 según registros.",
    ]
    for text in disclosures:
        assert is_cross_customer_attempt(text, session_customer) is True, (
            f"Expected True Positive for foreign customer disclosure: '{text}'"
        )


def test_output_guard_tn_safe_generic_explanation() -> None:
    """Generic explanations without customer tokens must NOT trigger output guard (TN)."""
    session_customer = "CUST-0001"
    safe_texts = [
        (
            "Los requisitos para un crédito vehicular son documento de identidad "
            "y sustento de ingresos."
        ),
        "Para presentar un reclamo, acércate a una agencia o llama a nuestra central telefónica.",
        "Las tasas de interés SBS varían según el producto y el plazo evaluado.",
        "No encuentro información suficiente en la base de conocimiento autorizada.",
    ]
    for text in safe_texts:
        assert is_cross_customer_attempt(text, session_customer) is False, (
            f"Expected True Negative (no trigger) for safe generic text: '{text}'"
        )


def test_output_guard_tn_own_customer_id_mention() -> None:
    """Mentioning the authenticated customer's own ID must NOT be flagged as cross-customer (TN)."""
    session_customer = "CUST-0001"
    own_id_texts = [
        "Estimado cliente CUST-0001, tu saldo pendiente es 10000 PEN.",
        "Confirmamos que la sesión corresponde a cust-0001.",
        "Cliente CUST-0001: tu solicitud ha sido registrada correctamente.",
    ]
    for text in own_id_texts:
        assert is_cross_customer_attempt(text, session_customer) is False, (
            f"Expected True Negative (no trigger) when mentioning own customer ID: '{text}'"
        )


def test_output_guard_tn_malformed_lookalikes_no_false_positives() -> None:
    """Malformed tokens or unrelated numbers must NOT trigger false positives (TN)."""
    session_customer = "CUST-0001"
    malformed_texts = [
        "Referencia de ticket: CUSTOMER-0002 en el sistema antiguo.",
        "Código interno: CUST_0002 y CUST-1 y CUST-12345.",
        "Identificador: CLIENTE-0002 o USUARIO-0001.",
        "Cuenta número 1234-5678-9012-3456 en soles.",
        "Número de documento CUST-ABC no es un ID canónico.",
    ]
    for text in malformed_texts:
        assert is_cross_customer_attempt(text, session_customer) is False, (
            f"Expected True Negative (no false positive) for malformed lookalike: '{text}'"
        )


def test_output_guard_tp_multiple_ids_and_cross_customer_detection() -> None:
    """Multiple customer IDs containing foreign IDs must trigger cross-customer detection (TP)."""
    session_customer = "CUST-0001"
    mixed_texts = [
        "Sesión activa de CUST-0001. Transferencia hacia CUST-0002 procesada.",
        "Clientes vinculados: CUST-0001, CUST-0003 y CUST-0004.",
        "Comparativa: CUST-0002 tiene saldo 5000 mientras CUST-0001 tiene 2000.",
    ]
    for text in mixed_texts:
        assert is_cross_customer_attempt(text, session_customer) is True, (
            f"Expected True Positive for mixed/multiple customer IDs: '{text}'"
        )


def test_output_guard_safe_mention_and_redaction_policy() -> None:
    """Redaction must replace foreign customer IDs and preserve authenticated customer ID."""
    session_customer = "CUST-0001"
    original = "Cliente CUST-0001 solicitó consultar a CUST-0002 y CUST-0003."
    redacted = redact_foreign_customer_ids(original, session_customer, "[PROTEGIDO]")

    assert "CUST-0001" in redacted, "Own customer ID must remain unredacted"
    assert "CUST-0002" not in redacted, "Foreign customer ID CUST-0002 must be redacted"
    assert "CUST-0003" not in redacted, "Foreign customer ID CUST-0003 must be redacted"
    assert redacted == "Cliente CUST-0001 solicitó consultar a [PROTEGIDO] y [PROTEGIDO]."
    assert is_cross_customer_attempt(redacted, session_customer) is False, (
        "Sanitized text must not trigger cross-customer interceptor"
    )
