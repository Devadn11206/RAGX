import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class RAGXException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class InfrastructureException(RAGXException):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(
            code="DEPENDENCY_UNAVAILABLE",
            message=message,
            status_code=status_code
        )

class ConfigurationException(RAGXException):
    def __init__(self, message: str):
        super().__init__(
            code="CONFIGURATION_ERROR",
            message=message,
            status_code=500
        )

async def ragx_exception_handler(request: Request, exc: RAGXException):
    logger.error(f"Error {exc.code}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred."
            }
        }
    )
