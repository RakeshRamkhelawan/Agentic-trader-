class AppError(Exception):
    """Base class for application exceptions."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class QuotaExceededError(AppError):
    """Raised when a tenant exceeds their usage quota."""
    def __init__(self, message: str = "Quota exceeded", details: dict = None):
        super().__init__(message, status_code=429, details=details)

class TenantIsolationError(AppError):
    """Raised when tenant isolation cannot be enforced."""
    def __init__(self, message: str = "Tenant isolation error", details: dict = None):
        super().__init__(message, status_code=403, details=details)
