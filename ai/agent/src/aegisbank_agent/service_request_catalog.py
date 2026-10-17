"""Deterministic, versioned service-request reasons shared by agent boundaries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceRequestReasonOption:
    code: str
    category: str
    label: str
    description: str
    requires_description: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "reason_code": self.code,
            "category": self.category,
            "label": self.label,
            "description": self.description,
            "requires_description": self.requires_description,
        }


REASON_OPTIONS: tuple[ServiceRequestReasonOption, ...] = (
    ServiceRequestReasonOption(
        "LOAN_RESTRUCTURING",
        "LOAN",
        "Reprogramación del préstamo",
        "Solicitar revisión o reprogramación de cuotas.",
    ),
    ServiceRequestReasonOption(
        "LOAN_BALANCE_DISPUTE",
        "LOAN",
        "Saldo o detalle del préstamo",
        "Reportar una diferencia en el saldo o detalle del préstamo.",
    ),
    ServiceRequestReasonOption(
        "LOAN_INTEREST_RATE",
        "LOAN",
        "Tasa de interés del préstamo",
        "Consultar o reclamar la tasa aplicada al préstamo.",
    ),
    ServiceRequestReasonOption(
        "LOAN_PAYMENT_DIFFICULTY",
        "LOAN",
        "Dificultad para pagar",
        "Solicitar orientación por dificultad temporal de pago.",
    ),
    ServiceRequestReasonOption(
        "INSTALLMENT_DATE",
        "INSTALLMENT",
        "Fecha de vencimiento",
        "Consultar o reclamar la fecha de vencimiento de una cuota.",
    ),
    ServiceRequestReasonOption(
        "INSTALLMENT_DUPLICATE_CHARGE",
        "INSTALLMENT",
        "Cobro duplicado de cuota",
        "Reportar un cobro duplicado de una cuota.",
    ),
    ServiceRequestReasonOption(
        "INSTALLMENT_AMOUNT_DISPUTE",
        "INSTALLMENT",
        "Importe de cuota incorrecto",
        "Reportar que el importe cobrado no coincide.",
    ),
    ServiceRequestReasonOption(
        "INSTALLMENT_PAYMENT_NOT_REFLECTED",
        "INSTALLMENT",
        "Pago no reflejado",
        "Reportar un pago de cuota que aún no aparece aplicado.",
    ),
    ServiceRequestReasonOption(
        "INSTALLMENT_OVERDUE_DISPUTE",
        "INSTALLMENT",
        "Mora o vencimiento incorrecto",
        "Reportar una cuota marcada como vencida de forma incorrecta.",
    ),
    ServiceRequestReasonOption(
        "FEE_UNRECOGNIZED",
        "FEE",
        "Comisión o cargo no reconocido",
        "Reportar una comisión o cargo que no reconoces.",
    ),
    ServiceRequestReasonOption(
        "FEE_DUPLICATE_CHARGE", "FEE", "Comisión o cargo duplicado", "Reportar un cargo repetido."
    ),
    ServiceRequestReasonOption(
        "FEE_AMOUNT_DISPUTE",
        "FEE",
        "Importe de comisión incorrecto",
        "Reportar que el importe de una comisión no coincide.",
    ),
    ServiceRequestReasonOption(
        "FEE_REFUND_REQUEST",
        "FEE",
        "Solicitud de devolución",
        "Solicitar revisión de una comisión para posible devolución.",
    ),
    ServiceRequestReasonOption(
        "GENERAL_FRAUD",
        "GENERAL",
        "Fraude o estafa",
        "Reportar una posible estafa o actividad fraudulenta.",
        True,
    ),
    ServiceRequestReasonOption(
        "GENERAL_ACCOUNT_ACCESS",
        "GENERAL",
        "Acceso o seguridad de cuenta",
        "Reportar un problema de acceso o seguridad.",
        True,
    ),
    ServiceRequestReasonOption(
        "GENERAL_DATA_UPDATE",
        "GENERAL",
        "Actualización de datos",
        "Solicitar orientación para actualizar datos del cliente.",
    ),
    ServiceRequestReasonOption(
        "GENERAL_STATUS",
        "GENERAL",
        "Estado de una solicitud",
        "Consultar el estado de un reclamo o solicitud existente.",
    ),
    ServiceRequestReasonOption(
        "GENERAL_OTHER",
        "GENERAL",
        "Otro motivo",
        "Describe brevemente el motivo del reclamo.",
        True,
    ),
)

REASON_BY_CODE = {option.code: option for option in REASON_OPTIONS}


def options_for_category(category: str) -> list[dict[str, object]]:
    return [option.as_dict() for option in REASON_OPTIONS if option.category == category]


def get_reason(code: str) -> ServiceRequestReasonOption | None:
    return REASON_BY_CODE.get(code.strip().upper())
