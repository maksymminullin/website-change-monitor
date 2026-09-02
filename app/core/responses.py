from fastapi import status
from fastapi.responses import JSONResponse


def error_response(
    detail: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


def conflict_response(detail: str) -> JSONResponse:
    return error_response(detail, status_code=status.HTTP_409_CONFLICT)


def not_found_response(detail: str) -> JSONResponse:
    return error_response(detail, status_code=status.HTTP_404_NOT_FOUND)


def bad_request_response(detail: str) -> JSONResponse:
    return error_response(detail, status_code=status.HTTP_400_BAD_REQUEST)


def internal_error_response(detail: str = "Internal server error") -> JSONResponse:
    return error_response(detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
