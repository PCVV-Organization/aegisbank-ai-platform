from enum import StrEnum


class CustomerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CustomerSegment(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    MICRO_BUSINESS = "MICRO_BUSINESS"
    SMALL_BUSINESS = "SMALL_BUSINESS"


class LoanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DELINQUENT = "DELINQUENT"


class Currency(StrEnum):
    PEN = "PEN"
    USD = "USD"


class InstallmentStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class ServiceRequestStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ServiceRequestCategory(StrEnum):
    LOAN = "LOAN"
    INSTALLMENT = "INSTALLMENT"
    FEE = "FEE"
    GENERAL = "GENERAL"
