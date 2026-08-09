from typing import Annotated

from dependencies.tracked_page import get_tracked_page_service
from exceptions.tracked_page import (
    EmptyTrackedPageUpdateError,
    TrackedPageAlreadyExistsError,
    TrackedPageNotFoundError,
)
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.tracked_page import TrackedPageCreate, TrackedPageRead, TrackedPageUpdate
from services.tracked_page import TrackedPageService

router = APIRouter(prefix="/tracked-pages", tags=["tracked-pages"])


@router.post("", response_model=TrackedPageRead, status_code=status.HTTP_201_CREATED)
async def create_tracked_page(
    page_in: TrackedPageCreate,
    user_id: int,
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
) -> TrackedPageRead:
    try:
        return await service.create(user_id=user_id, page_in=page_in)
    except TrackedPageAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("", response_model=list[TrackedPageRead])
async def get_all_tracked_pages(
    user_id: int, service: Annotated[TrackedPageService, Depends(get_tracked_page_service)]
) -> list[TrackedPageRead]:
    return await service.get_all(user_id=user_id)


@router.patch("/{page_id}", response_model=TrackedPageRead)
async def update_tracked_page(
    page_id: int,
    page_in: TrackedPageUpdate,
    user_id: int,
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
) -> TrackedPageRead:
    try:
        return await service.update(user_id=user_id, page_id=page_id, page_in=page_in)
    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EmptyTrackedPageUpdateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracked_page(
    page_id: int,
    user_id: int,
    service: Annotated[TrackedPageService, Depends(get_tracked_page_service)],
) -> None:
    try:
        await service.delete(user_id=user_id, page_id=page_id)
    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
