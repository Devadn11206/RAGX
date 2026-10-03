from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ErrorCategory(str, Enum):
    RETRYABLE_TRANSIENT = "RETRYABLE_TRANSIENT"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    SERVER_ERROR = "SERVER_ERROR"

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    fallback_used: bool = False
    primary_provider: str = "gemini"
    fallback_reason: Optional[str] = None
    attempts: int = 1
    latency_ms: int = 0
    estimated_cost: float = 0.0

class ProviderError(Exception):
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SERVER_ERROR, retry_delay: Optional[float] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.retry_delay = retry_delay

class ProviderTimeoutError(ProviderError):
    def __init__(self, message: str = "Provider call timed out"):
        super().__init__(message, category=ErrorCategory.TIMEOUT)

class ProviderRateLimitError(ProviderError):
    def __init__(self, message: str = "Provider rate limit exceeded", retry_delay: Optional[float] = None):
        super().__init__(message, category=ErrorCategory.RATE_LIMITED, retry_delay=retry_delay)

class ProviderQuotaExhaustedError(ProviderError):
    def __init__(self, message: str = "Provider quota exhausted", retry_delay: Optional[float] = None):
        super().__init__(message, category=ErrorCategory.QUOTA_EXHAUSTED, retry_delay=retry_delay)

class ProviderAuthenticationError(ProviderError):
    def __init__(self, message: str = "Provider authentication error"):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION_ERROR)

class ProviderUnavailableError(ProviderError):
    def __init__(self, message: str = "Provider unavailable"):
        super().__init__(message, category=ErrorCategory.RETRYABLE_TRANSIENT)

class ProviderInvalidRequestError(ProviderError):
    def __init__(self, message: str = "Provider invalid request"):
        super().__init__(message, category=ErrorCategory.INVALID_REQUEST)

class ProviderServerError(ProviderError):
    def __init__(self, message: str = "Provider internal server error"):
        super().__init__(message, category=ErrorCategory.SERVER_ERROR)
