from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse

from app.dependencies.auth import get_current_user
from app.dependencies.snapshot import get_snapshot_service
from app.dependencies.tracked_page import get_tracked_page_service
from app.models.user import User
from app.schemas.snapshot import SnapshotRead
from app.schemas.tracked_page import TrackedPageCreate, TrackedPageRead, TrackedPageUpdate
from app.services.snapshot import SnapshotService
from app.services.tracked_page import TrackedPageService

router = APIRouter(prefix="/tracked-pages", tags=["tracked-pages"])


@router.post("", response_model=TrackedPageRead, status_code=status.HTTP_201_CREATED)
async def create_tracked_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
    page_in: TrackedPageCreate | None = None,
    url: Annotated[str | None, Form()] = None,
):
    target_url = url if url else (page_in.url if page_in else None)

    if not target_url:
        raise HTTPException(status_code=400, detail="URL is required")

    create_schema = TrackedPageCreate(url=target_url)
    result = await service.create(user_id=current_user.id, page_in=create_schema)

    if request.headers.get("hx-request"):
        return HTMLResponse(
            f"<div class='alert alert-success mt-4'>Page {result.url} successfully added</div>"
        )

    return result


@router.get("", response_model=list[TrackedPageRead])
async def get_all_tracked_pages(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
) -> list[TrackedPageRead]:
    return await service.get_all(user_id=current_user.id)


@router.patch("/{page_id}", response_model=TrackedPageRead)
async def update_tracked_page(
    request: Request,
    page_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
    page_in: TrackedPageUpdate | None = None,
    status: Annotated[Literal["active", "archived"] | None, Form()] = None,
):
    update_data = page_in
    if request.headers.get("hx-request") and status is not None:
        update_data = TrackedPageUpdate(status=status)

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated_page = await service.update(
        user_id=current_user.id, page_id=page_id, page_in=update_data
    )

    if request.headers.get("hx-request"):
        resp = HTMLResponse("")
        resp.headers["HX-Refresh"] = "true"
        return resp

    return updated_page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracked_page(
    request: Request,
    page_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
) -> Response:
    await service.delete(user_id=current_user.id, page_id=page_id)

    if request.headers.get("hx-request"):
        return HTMLResponse("")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{page_id}/snapshots", response_model=list[SnapshotRead])
async def get_all_snapshots(
    page_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> list[SnapshotRead]:
    return await service.get_all(user_id=current_user.id, tracked_page_id=page_id)
