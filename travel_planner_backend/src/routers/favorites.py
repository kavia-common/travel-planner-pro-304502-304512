from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.common import DeleteResponse
from src.schemas.favorites import FavoriteCreate, FavoriteOut
from src.storage.db import get_db_session
from src.storage.models import Destination, Favorite, Trip, User

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "",
    response_model=list[FavoriteOut],
    summary="List favorites",
    description="List favorite destinations for the current user.",
    operation_id="favorites_list",
)
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[FavoriteOut]:
    """List favorites for user."""
    res = await db.execute(select(Favorite).where(Favorite.user_id == current_user.id).order_by(Favorite.created_at.desc()))
    return [FavoriteOut.model_validate(f) for f in res.scalars().all()]


@router.post(
    "",
    response_model=FavoriteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add favorite",
    description="Favorite a destination. Destination must belong to one of user's trips.",
    operation_id="favorites_create",
)
async def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FavoriteOut:
    """Add a favorite destination for user."""
    # Ensure destination belongs to user via trip ownership
    stmt = (
        select(Destination.id)
        .join(Trip, Destination.trip_id == Trip.id)
        .where(Destination.id == payload.destination_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    fav = Favorite(user_id=current_user.id, destination_id=payload.destination_id)
    db.add(fav)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # already favorited
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already favorited")
    await db.refresh(fav)
    return FavoriteOut.model_validate(fav)


@router.delete(
    "/{favorite_id}",
    response_model=DeleteResponse,
    summary="Remove favorite",
    description="Remove a favorite by ID (must belong to current user).",
    operation_id="favorites_delete",
)
async def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DeleteResponse:
    """Remove favorite."""
    res = await db.execute(select(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == current_user.id))
    fav = res.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    await db.delete(fav)
    await db.commit()
    return DeleteResponse(deleted=True)
