class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CustomerNotFoundError(DomainError):
    def __init__(self):
        super().__init__("CUSTOMER_NOT_FOUND", "Synthetic customer was not found.", 404)


class LoanNotFoundError(DomainError):
    def __init__(self):
        super().__init__("LOAN_NOT_FOUND", "Synthetic loan was not found.", 404)


class InstallmentNotFoundError(DomainError):
    def __init__(self):
        super().__init__(
            "INSTALLMENT_NOT_FOUND",
            "No applicable synthetic installment was found.",
            404,
        )


class ServiceRequestNotFoundError(DomainError):
    def __init__(self):
        super().__init__(
            "SERVICE_REQUEST_NOT_FOUND",
            "Synthetic service request was not found.",
            404,
        )


class DataStoreUnavailableError(DomainError):
    def __init__(self):
        super().__init__("DATASTORE_UNAVAILABLE", "Local datastore is unavailable.", 503)


class DomainValidationError(DomainError):
    def __init__(self, message: str):
        super().__init__("VALIDATION_ERROR", message, 422)


class InternalError(DomainError):
    def __init__(self):
        super().__init__("INTERNAL_ERROR", "An internal error occurred.", 500)
