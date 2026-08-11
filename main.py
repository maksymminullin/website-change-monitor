from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_setting
from app.routers.auth import router as auth_router
from app.routers.tracked_page import router as tracked_page_router
from app.routers.web import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


settings = get_setting()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web_router)
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(tracked_page_router, prefix="/api/v1", tags=["Tracked Pages"])
