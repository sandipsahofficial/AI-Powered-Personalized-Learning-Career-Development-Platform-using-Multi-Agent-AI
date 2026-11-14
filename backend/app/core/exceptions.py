from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionError(AppException):
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


class RedisConnectionError(AppException):
    def __init__(self, message: str = "Redis connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


class LLMServiceUnavailableError(AppException):
    def __init__(self, message: str = "Ollama LLM service unreachable", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


class ResourceNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Operation not permitted", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected internal server error occurred.",
            "path": request.url.path
        }
    )
