from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from aegisbank_intent_classifier.constants import (
    DATASET_MANIFEST_PATH,
    DATASET_PATH,
    EXPECTED_HOLDOUT_COUNT,
    EXPECTED_RECORD_COUNT,
    EXPECTED_TRAIN_COUNT,
    GENERATION_VERSION,
    GROUPS_PER_CLASS,
    HOLDOUT_GROUPS_PER_CLASS,
    LABELS,
    PROHIBITED_FIELDS,
    RANDOM_STATE,
    TRAIN_GROUPS_PER_CLASS,
    VARIATIONS_PER_GROUP,
)

RECORD_FIELDS = {"example_id", "text", "label", "template_group_id", "split"}
ALLOWED_SPLITS = {"train", "holdout"}


class DatasetValidationError(ValueError):
    """Raised when the generated dataset violates its frozen contract."""


@dataclass(frozen=True, slots=True)
class IntentExample:
    example_id: str
    text: str
    label: str
    template_group_id: str
    split: str

    def as_dict(self) -> dict[str, str]:
        return {
            "example_id": self.example_id,
            "text": self.text,
            "label": self.label,
            "template_group_id": self.template_group_id,
            "split": self.split,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> IntentExample:
        fields = set(payload)
        prohibited = fields & PROHIBITED_FIELDS
        if prohibited:
            raise DatasetValidationError(f"Prohibited dataset fields: {sorted(prohibited)}")
        if fields != RECORD_FIELDS:
            raise DatasetValidationError(
                f"Dataset fields must be {sorted(RECORD_FIELDS)}, received {sorted(fields)}"
            )
        if not all(isinstance(payload[field], str) for field in RECORD_FIELDS):
            raise DatasetValidationError("Every dataset field must be a string")
        return cls(**payload)


TOPICS_BY_LABEL: dict[str, tuple[tuple[str, str], ...]] = {
    "informational": (
        ("credito_negocio", "un crédito para negocio"),
        ("tasa_interes", "una tasa de interés"),
        ("comision_bancaria", "una comisión bancaria"),
        ("capital_prestamo", "el capital de un préstamo"),
        ("plazo_credito", "el plazo de un crédito"),
        ("garantia_crediticia", "una garantía crediticia"),
        ("cronograma_pagos", "un cronograma de pagos"),
        ("cuota_prestamo", "una cuota de préstamo"),
        ("interes_moratorio", "el interés moratorio"),
        ("refinanciamiento", "el refinanciamiento"),
        ("prepago_deuda", "el prepago de una deuda"),
        ("seguro_desgravamen", "el seguro de desgravamen"),
        ("desembolso_credito", "un desembolso de crédito"),
        ("evaluacion_crediticia", "una evaluación crediticia"),
        ("requisitos_credito", "los requisitos generales para solicitar crédito"),
        ("credito_moneda_extranjera", "un crédito en moneda extranjera"),
        ("periodo_gracia", "un periodo de gracia"),
        ("amortizacion_capital", "la amortización de capital"),
        ("reprogramacion_cuotas", "una reprogramación de cuotas"),
        ("saldo_capital", "el saldo de capital"),
        ("vencimiento_cuota", "la fecha de vencimiento de una cuota"),
        ("penalidad_atraso", "una penalidad por atraso"),
        ("capital_trabajo", "un crédito para capital de trabajo"),
        ("activo_fijo", "un crédito para activo fijo"),
        ("historial_pagos", "el historial de pagos"),
    ),
    "account_query": (
        ("proxima_cuota", "la fecha de la próxima cuota"),
        ("saldo_pendiente", "el saldo pendiente del préstamo"),
        ("estado_credito", "el estado actual del crédito"),
        ("cuotas_pendientes", "la cantidad de cuotas pendientes"),
        ("cuotas_pagadas", "la cantidad de cuotas pagadas"),
        ("monto_siguiente_cuota", "el monto de la siguiente cuota"),
        ("fecha_desembolso", "la fecha del desembolso registrado"),
        ("plazo_restante", "el plazo restante del préstamo"),
        ("moneda_credito", "la moneda del crédito"),
        ("tasa_aplicada", "la tasa aplicada al préstamo"),
        ("comisiones_registradas", "las comisiones registradas"),
        ("mora_acumulada", "el interés moratorio acumulado"),
        ("cuota_vencida", "la cuota que figura vencida"),
        ("ultimo_pago", "el último pago registrado"),
        ("cronograma_vigente", "el cronograma vigente"),
        ("capital_pendiente", "el capital pendiente"),
        ("intereses_pendientes", "los intereses pendientes"),
        ("estado_solicitud", "el estado de una solicitud asociada"),
        ("numero_proxima_cuota", "el número de la próxima cuota"),
        ("cancelacion_estimada", "la fecha de cancelación estimada"),
        ("total_pagado", "el total pagado hasta ahora"),
        ("total_por_pagar", "el total pendiente de pago"),
        ("cuotas_atrasadas", "las cuotas con atraso"),
        ("detalle_cuota", "el detalle de una cuota específica"),
        ("resumen_credito", "el resumen del crédito"),
    ),
    "service_request": (
        ("comision_no_reconocida", "un reclamo por una comisión no reconocida"),
        ("pago_no_reflejado", "una solicitud por un pago no reflejado"),
        ("error_cronograma", "un caso por un error en el cronograma"),
        ("cuota_duplicada", "un reclamo por una cuota duplicada"),
        ("revision_intereses", "una solicitud para revisar intereses"),
        ("monto_incorrecto", "un reporte por un monto incorrecto"),
        ("vencimiento_erroneo", "un caso sobre una fecha de vencimiento errónea"),
        ("aclaracion_saldo", "una solicitud de aclaración de saldo"),
        ("estado_credito_incorrecto", "un reclamo por estado incorrecto del crédito"),
        ("revision_penalidad", "una solicitud para revisar una penalidad"),
        ("demora_atencion", "un caso por demora en la atención"),
        ("desembolso_pendiente", "un reclamo sobre un desembolso pendiente"),
        ("constancia_pago", "una solicitud de constancia de pago"),
        ("correccion_registro", "un caso para revisar un registro simulado"),
        ("explicacion_cargos", "una solicitud de explicación de cargos"),
        ("calculo_cuota", "un reclamo sobre el cálculo de una cuota"),
        ("seguimiento_caso", "una solicitud para actualizar el seguimiento de un caso"),
        ("respuesta_incompleta", "un caso por una respuesta incompleta"),
        ("revision_prestamo", "una solicitud de revisión del préstamo"),
        ("pago_otra_cuota", "un reclamo por un pago aplicado a otra cuota"),
        ("reabrir_caso", "una solicitud para reabrir un caso cerrado"),
        ("falta_respuesta", "un reclamo por falta de respuesta"),
        ("adjuntar_informacion", "una solicitud para adjuntar información sintética"),
        ("diferencia_saldo", "un caso por diferencia en el saldo mostrado"),
        ("atencion_general", "una solicitud general de atención"),
    ),
    "sensitive_action": (
        ("transferencia_dinero", "una transferencia de dinero"),
        ("cambio_dato_sensible", "el cambio de un dato sensible"),
        ("aprobar_credito", "la aprobación inmediata de un crédito"),
        ("pago_automatico", "el pago automático de una cuota"),
        ("retiro_fondos", "el retiro de fondos"),
        ("cierre_cuenta", "el cierre definitivo de una cuenta"),
        ("cambio_titular", "el cambio de titular de una cuenta"),
        ("desembolso_prestamo", "el desembolso de un préstamo"),
        ("modificar_deuda", "la modificación del monto de una deuda"),
        ("condonar_intereses", "la condonación de intereses"),
        ("eliminar_penalidad", "la eliminación de una penalidad"),
        ("bloquear_fondos", "el bloqueo de fondos"),
        ("desbloquear_operacion", "el desbloqueo de una operación"),
        ("cambiar_destino_credito", "la modificación del destino de un crédito"),
        ("cancelar_prestamo", "la cancelación irreversible de un préstamo"),
        ("cambiar_credenciales", "el cambio de credenciales de acceso"),
        ("autorizar_compra", "la autorización de una compra"),
        ("revertir_pago", "la reversión de un pago"),
        ("modificar_cronograma", "la modificación del cronograma acordado"),
        ("firmar_contrato", "la firma de un contrato"),
        ("abrir_producto", "la apertura automática de un producto"),
        ("activar_tarjeta", "la activación de una tarjeta"),
        ("aumentar_limite", "el aumento de un límite financiero"),
        ("ejecutar_debito", "la ejecución de un débito"),
        ("crear_beneficiario", "la creación de un beneficiario"),
    ),
    "unsupported": (
        ("clima", "el pronóstico del clima para mañana"),
        ("receta", "una receta de pasta casera"),
        ("futbol", "el resultado de un partido de fútbol"),
        ("horoscopo", "el horóscopo de esta semana"),
        ("peliculas", "recomendaciones de películas"),
        ("cancion", "la letra de una canción popular"),
        ("ruta_turistica", "una ruta turística por la ciudad"),
        ("programacion", "un error en un programa informático"),
        ("geometria", "la solución de un problema de geometría"),
        ("historia", "la historia de un imperio antiguo"),
        ("planetas", "la distancia entre dos planetas"),
        ("jardineria", "el cuidado de una planta doméstica"),
        ("traduccion", "la traducción de una frase al francés"),
        ("poema", "un poema para un cumpleaños"),
        ("pintura", "una técnica de pintura al óleo"),
        ("ajedrez", "una apertura de ajedrez"),
        ("ejercicio", "una rutina de ejercicio físico"),
        ("fotografia", "consejos para tomar fotografías"),
        ("trafico", "el reporte de tráfico de la ciudad"),
        ("astronomia", "una explicación sobre una constelación"),
        ("cartelera", "la cartelera del cine"),
        ("concurso_musical", "el ganador de un concurso musical"),
        ("bicicleta", "la reparación de una bicicleta"),
        ("decoracion", "la decoración de una sala"),
        ("festival", "la agenda de un festival cultural"),
    ),
}

VARIATION_TEMPLATES: dict[str, tuple[str, ...]] = {
    "informational": (
        "¿Qué significa {topic}?",
        "Explícame de manera general cómo funciona {topic}.",
        "Quisiera conocer las características de {topic}.",
        "Dame información institucional sobre {topic}.",
    ),
    "account_query": (
        "¿Puedes indicarme {topic} en mi perfil bancario ficticio?",
        "Necesito consultar {topic} de mi préstamo sintético.",
        "Muéstrame {topic} asociado a mi información simulada.",
        "Quisiera revisar {topic} de mi relación crediticia ficticia.",
    ),
    "service_request": (
        "Quiero registrar {topic}.",
        "Necesito abrir {topic}.",
        "Ayúdame a crear {topic} para un caso ficticio.",
        "Deseo ingresar {topic} y consultar su seguimiento.",
    ),
    "sensitive_action": (
        "Quiero que ejecutes {topic}.",
        "Realiza {topic} por mí.",
        "Autoriza directamente {topic}.",
        "Completa sin revisión humana {topic} en mi escenario ficticio.",
    ),
    "unsupported": (
        "¿Puedes contarme sobre {topic}?",
        "Quiero saber más acerca de {topic}.",
        "Explícame {topic}.",
        "Dame una respuesta relacionada con {topic}.",
    ),
}


def generate_records() -> list[IntentExample]:
    records: list[IntentExample] = []
    example_number = 1

    if tuple(TOPICS_BY_LABEL) != LABELS:
        raise DatasetValidationError("Generator label order differs from the frozen taxonomy")

    for label in LABELS:
        topics = TOPICS_BY_LABEL[label]
        templates = VARIATION_TEMPLATES[label]
        if len(topics) != GROUPS_PER_CLASS:
            raise DatasetValidationError(f"{label} must define exactly {GROUPS_PER_CLASS} groups")
        if len(templates) != VARIATIONS_PER_GROUP:
            raise DatasetValidationError(
                f"{label} must define exactly {VARIATIONS_PER_GROUP} variations"
            )

        for group_number, (slug, topic) in enumerate(topics, start=1):
            split = "train" if group_number <= TRAIN_GROUPS_PER_CLASS else "holdout"
            group_id = f"{label}_{slug}_{group_number:02d}"
            for template in templates:
                records.append(
                    IntentExample(
                        example_id=f"EX-{example_number:04d}",
                        text=template.format(topic=topic),
                        label=label,
                        template_group_id=group_id,
                        split=split,
                    )
                )
                example_number += 1

    return records


def serialize_records(records: list[IntentExample]) -> bytes:
    lines = [
        json.dumps(record.as_dict(), ensure_ascii=False, separators=(",", ":"))
        for record in records
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_manifest(records: list[IntentExample], dataset_bytes: bytes) -> dict[str, Any]:
    labels = Counter(record.label for record in records)
    splits = Counter(record.split for record in records)
    groups = {record.template_group_id for record in records}
    groups_by_class = {
        label: len({record.template_group_id for record in records if record.label == label})
        for label in LABELS
    }
    return {
        "class_distribution": {label: labels[label] for label in LABELS},
        "generation_version": GENERATION_VERSION,
        "holdout_count": splits["holdout"],
        "random_state": RANDOM_STATE,
        "record_count": len(records),
        "sha256": sha256(dataset_bytes).hexdigest(),
        "template_group_count": len(groups),
        "template_group_distribution": groups_by_class,
        "train_count": splits["train"],
    }


def write_dataset(
    dataset_path: Path = DATASET_PATH,
    manifest_path: Path = DATASET_MANIFEST_PATH,
) -> dict[str, Any]:
    records = generate_records()
    dataset_bytes = serialize_records(records)
    manifest = build_manifest(records, dataset_bytes)
    validate_dataset(records, dataset_bytes, manifest)

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_bytes(dataset_bytes)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def load_dataset(dataset_path: Path = DATASET_PATH) -> tuple[list[IntentExample], bytes]:
    dataset_bytes = dataset_path.read_bytes()
    text = dataset_bytes.decode("utf-8", errors="strict")
    records: list[IntentExample] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise DatasetValidationError(f"Empty JSONL line at {line_number}")
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise DatasetValidationError(f"Line {line_number} must contain a JSON object")
        records.append(IntentExample.from_dict(payload))
    return records, dataset_bytes


def load_manifest(manifest_path: Path = DATASET_MANIFEST_PATH) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DatasetValidationError("Dataset manifest must contain a JSON object")
    return payload


def validate_dataset(
    records: list[IntentExample],
    dataset_bytes: bytes,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []

    try:
        dataset_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        errors.append("Dataset is not valid UTF-8")

    if len(records) != EXPECTED_RECORD_COUNT:
        errors.append(f"Expected {EXPECTED_RECORD_COUNT} records, received {len(records)}")

    ids = [record.example_id for record in records]
    texts = [record.text for record in records]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate example_id values detected")
    if len(texts) != len(set(texts)):
        errors.append("Duplicate text values detected")
    if any(not re.fullmatch(r"EX-\d{4}", example_id) for example_id in ids):
        errors.append("example_id values must match EX-0001 format")
    if any(not text.strip() or text != text.strip() for text in texts):
        errors.append("Every text must be non-empty and trimmed")

    observed_labels = {record.label for record in records}
    if observed_labels != set(LABELS):
        errors.append(f"Observed labels differ from frozen labels: {sorted(observed_labels)}")
    if any(record.split not in ALLOWED_SPLITS for record in records):
        errors.append("Dataset contains an unsupported split")

    label_counts = Counter(record.label for record in records)
    split_counts = Counter(record.split for record in records)
    for label in LABELS:
        if label_counts[label] != 100:
            errors.append(f"{label} must contain exactly 100 examples")
        train_count = sum(record.label == label and record.split == "train" for record in records)
        holdout_count = sum(
            record.label == label and record.split == "holdout" for record in records
        )
        if train_count != 80 or holdout_count != 20:
            errors.append(f"{label} must contain 80 train and 20 holdout examples")

    if split_counts["train"] != EXPECTED_TRAIN_COUNT:
        errors.append(f"TRAIN must contain exactly {EXPECTED_TRAIN_COUNT} examples")
    if split_counts["holdout"] != EXPECTED_HOLDOUT_COUNT:
        errors.append(f"HOLDOUT must contain exactly {EXPECTED_HOLDOUT_COUNT} examples")

    records_by_group: dict[str, list[IntentExample]] = defaultdict(list)
    for record in records:
        records_by_group[record.template_group_id].append(record)

    if len(records_by_group) != GROUPS_PER_CLASS * len(LABELS):
        errors.append("Dataset must contain exactly 125 template groups")

    for group_id, group_records in records_by_group.items():
        if len(group_records) != VARIATIONS_PER_GROUP:
            errors.append(f"{group_id} must contain exactly {VARIATIONS_PER_GROUP} records")
        if len({record.split for record in group_records}) != 1:
            errors.append(f"{group_id} crosses train and holdout")
        if len({record.label for record in group_records}) != 1:
            errors.append(f"{group_id} contains multiple labels")

    train_groups = {record.template_group_id for record in records if record.split == "train"}
    holdout_groups = {record.template_group_id for record in records if record.split == "holdout"}
    if train_groups & holdout_groups:
        errors.append("template_group_id leakage exists between train and holdout")

    for label in LABELS:
        label_train_groups = {
            record.template_group_id
            for record in records
            if record.label == label and record.split == "train"
        }
        label_holdout_groups = {
            record.template_group_id
            for record in records
            if record.label == label and record.split == "holdout"
        }
        if len(label_train_groups) != TRAIN_GROUPS_PER_CLASS:
            errors.append(f"{label} must contain 20 TRAIN groups")
        if len(label_holdout_groups) != HOLDOUT_GROUPS_PER_CLASS:
            errors.append(f"{label} must contain 5 HOLDOUT groups")

    prohibited_tokens = tuple(field.casefold() for field in PROHIBITED_FIELDS)
    if any(token in text.casefold() for text in texts for token in prohibited_tokens):
        errors.append("Dataset text contains a prohibited personal-data token")

    actual_sha = sha256(dataset_bytes).hexdigest()
    expected_manifest = build_manifest(records, dataset_bytes)
    for key, expected_value in expected_manifest.items():
        if manifest.get(key) != expected_value:
            errors.append(f"Manifest field {key!r} does not match the dataset")
    if manifest.get("sha256") != actual_sha:
        errors.append("Manifest SHA-256 does not match dataset bytes")

    if errors:
        raise DatasetValidationError("; ".join(errors))

    return {
        "class_distribution": {label: label_counts[label] for label in LABELS},
        "duplicate_ids": 0,
        "duplicate_texts": 0,
        "group_leakage": 0,
        "holdout_count": split_counts["holdout"],
        "record_count": len(records),
        "sha256": actual_sha,
        "template_group_count": len(records_by_group),
        "train_count": split_counts["train"],
    }


def validate_dataset_files(
    dataset_path: Path = DATASET_PATH,
    manifest_path: Path = DATASET_MANIFEST_PATH,
) -> dict[str, Any]:
    records, dataset_bytes = load_dataset(dataset_path)
    manifest = load_manifest(manifest_path)
    return validate_dataset(records, dataset_bytes, manifest)
