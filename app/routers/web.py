from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates
from app.dependencies.auth import get_optional_web_user
from app.dependencies.tracked_page import get_tracked_page_service
from app.models.user import User
from app.services.tracked_page import TrackedPageService

router = APIRouter(tags=["Web UI"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, user: Annotated[User | None, Depends(get_optional_web_user)]
):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="auth.html")


@router.get("/", response_class=HTMLResponse)
async def add_page(request: Request, user: Annotated[User | None, Depends(get_optional_web_user)]):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request, name="add.html", context={"user": user, "active_page": "add"}
    )


@router.get("/list", response_class=HTMLResponse)
async def list_page(
    request: Request,
    user: Annotated[User | None, Depends(get_optional_web_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    pages = await service.get_all(user_id=user.id)

    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={"user": user, "active_page": "list", "pages": pages},
    )
