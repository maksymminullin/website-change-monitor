from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.exceptions.auth import InvalidCredentialsError, InvalidRefreshTokenError
from app.exceptions.tracked_page import (
    TrackedPageAlreadyExistsError,
    TrackedPageNotFoundError,
)
from app.exceptions.user import UserAlreadyExistsError
from app.routers.auth import router as auth_router
from app.routers.tracked_page import router as tracked_page_router
from app.routers.web import router as web_router

setup_logging()

settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(f"Validation error for {request.method} {request.url.path}: {exc}")
    errors = []
    for error in exc.errors():
        err = dict(error)
        if "input" in err and isinstance(err["input"], bytes):
            err["input"] = err["input"].decode(errors="replace")
        errors.append(err)

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request data",
            "errors": errors,
        },
    )


@app.exception_handler(TrackedPageNotFoundError)
async def tracked_page_not_found_exception_handler(
    request: Request,
    exc: TrackedPageNotFoundError,
) -> JSONResponse:
    logger.warning(f"Page not found: {exc}")
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Tracked page not found"},
    )


@app.exception_handler(TrackedPageAlreadyExistsError)
async def tracked_page_already_exists_exception_handler(
    request: Request,
    exc: TrackedPageAlreadyExistsError,
) -> JSONResponse:
    logger.warning(f"Duplicate page tracking: {exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "You already track this page"},
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_exception_handler(
    request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    logger.warning(f"Invalid credentials: {exc}")
    return JSONResponse(
        status_code=401,
        content={
            "detail": str(exc) or "Incorrect username or password",
            "WWW-Authenticate": "Bearer",
        },
    )


@app.exception_handler(InvalidRefreshTokenError)
async def invalid_refresh_token_exception_handler(
    request: Request,
    exc: InvalidRefreshTokenError,
) -> JSONResponse:
    logger.warning(f"Invalid refresh token: {exc}")
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc) or "Invalid or expired refresh token"},
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_exception_handler(
    request: Request,
    exc: UserAlreadyExistsError,
) -> JSONResponse:
    logger.warning(f"Duplicate user registration: {exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "Username already exists"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(f"Unexpected error for {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tracked_page_router, prefix="/api/v1")
