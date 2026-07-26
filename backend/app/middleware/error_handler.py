import logging
import time
from typing import Any, Dict
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("app.middleware.error_handler")


# --- Custom Platform Exceptions ---
class AegisException(Exception):
    """Base exception for AegisOne platform errors."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class EntityNotFoundException(AegisException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)


# --- Standardized RFC 7807 Exception Handlers ---
async def aegis_exception_handler(request: Request, exc: AegisException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://aegisone.local/errors/{exc.__class__.__name__.lower()}",
            "title": "Application Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://aegisone.local/errors/validation-error",
            "title": "Unprocessable Entity",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "Request body validation failed",
            "errors": errors,
            "instance": request.url.path,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error occurred: ")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://aegisone.local/errors/database-error",
            "title": "Database Transaction Failure",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An internal database error occurred while processing the request.",
            "instance": request.url.path,
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled system error on path {request.url.path}: ")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://aegisone.local/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "A critical system error occurred.",
            "instance": request.url.path,
        },
    )


# --- Request Logging and Timing Middleware ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.time()
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.info(
                f"Completed Request: {request.method} {request.url.path} "
                f"Status: {response.status_code} Duration: {duration:.4f}s"
            )
            response.headers["X-Response-Time"] = f"{duration:.4f}s"
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Failed Request: {request.method} {request.url.path} "
                f"Error: {str(e)} Duration: {duration:.4f}s"
            )
            raise e
