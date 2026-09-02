"""HTTP response helpers for standardized error and success responses."""

from fastapi import status
from fastapi.responses import JSONResponse


def error_response(
    detail: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """Return standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


def conflict_response(detail: str) -> JSONResponse:
    """Return 409 Conflict response."""
    return error_response(detail, status_code=status.HTTP_409_CONFLICT)


def not_found_response(detail: str) -> JSONResponse:
    """Return 404 Not Found response."""
    return error_response(detail, status_code=status.HTTP_404_NOT_FOUND)


def bad_request_response(detail: str) -> JSONResponse:
    """Return 400 Bad Request response."""
    return error_response(detail, status_code=status.HTTP_400_BAD_REQUEST)


def internal_error_response(detail: str = "Internal server error") -> JSONResponse:
    """Return 500 Internal Server Error response."""
    return error_response(detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
