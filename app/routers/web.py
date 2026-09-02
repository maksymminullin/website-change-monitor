from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from app.core.templates import templates
from app.dependencies.auth import get_auth_service, get_current_user, get_optional_web_user
from app.dependencies.tracked_page import get_tracked_page_service
from app.enums.page_status import PageStatus
from app.models.user import User
from app.schemas.tracked_page import TrackedPageCreate, TrackedPageUpdate
from app.schemas.user import UserCreate
from app.services.auth import AuthService
from app.services.tracked_page import TrackedPageService

router = APIRouter(tags=["Web UI"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, user: Annotated[User | None, Depends(get_optional_web_user)]
):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="auth.html")


@router.post("/login", response_class=HTMLResponse)
async def web_login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        token_data = await auth_service.login(
            username=form_data.username, password=form_data.password
        )
    except HTTPException as e:
        return HTMLResponse(
            f"<span class='text-error'>{e.detail}</span>", status_code=status.HTTP_200_OK
        )

    response = HTMLResponse("")
    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")
    response.headers["HX-Redirect"] = "/"
    return response


@router.post("/register", response_class=HTMLResponse)
async def web_register(
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        user_in = UserCreate(username=username, password=password)
        token_data = await auth_service.register(user_in)
    except ValidationError:
        error_msg = (
            "Invalid input: Username must be at least 3 characters "
            "and password at least 6 characters."
        )
        return HTMLResponse(
            f"<span class='text-error'>{error_msg}</span>", status_code=status.HTTP_200_OK
        )
    except HTTPException as e:
        return HTMLResponse(
            f"<span class='text-error'>{e.detail}</span>", status_code=status.HTTP_200_OK
        )

    response = HTMLResponse("")
    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")
    response.headers["HX-Redirect"] = "/"
    return response


@router.post("/logout")
async def web_logout(response: Response):
    response = HTMLResponse("")
    response.delete_cookie("access_token")
    response.headers["HX-Redirect"] = "/login"
    return response


@router.get("/", response_class=HTMLResponse)
async def add_page(request: Request, user: Annotated[User | None, Depends(get_optional_web_user)]):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request, name="add.html", context={"user": user, "active_page": "add"}
    )


@router.post("/tracked-pages", response_class=HTMLResponse)
async def web_add_tracked_page(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
    url: Annotated[str, Form()] = None,
):
    if not url:
        return HTMLResponse("<div class='alert alert-error mt-4'>URL is required</div>")

    try:
        create_schema = TrackedPageCreate(url=url)
        result = await service.create(user_id=current_user.id, page_in=create_schema)
        return HTMLResponse(
            f"<div class='alert alert-success mt-4'>Page {result.url} successfully added</div>"
        )
    except HTTPException as e:
        return HTMLResponse(f"<div class='alert alert-error mt-4'>{e.detail}</div>")


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


@router.patch("/tracked-pages/{page_id}", response_class=HTMLResponse)
async def web_update_tracked_page(
    page_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
    status: Annotated[PageStatus, Form()],
):
    update_data = TrackedPageUpdate(status=status)
    await service.update(user_id=current_user.id, page_id=page_id, page_in=update_data)
    resp = HTMLResponse("")
    resp.headers["HX-Refresh"] = "true"
    return resp


@router.delete("/tracked-pages/{page_id}", response_class=HTMLResponse)
async def web_delete_tracked_page(
    page_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
):
    await service.delete(user_id=current_user.id, page_id=page_id)
    return HTMLResponse("")
