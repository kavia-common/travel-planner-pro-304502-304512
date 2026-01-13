from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.common import DeleteResponse
from src.schemas.destinations import DestinationCreate, DestinationOut, DestinationUpdate
from src.storage.db import get_db_session
from src.storage.models import Destination, Trip, User

router = APIRouter(prefix="/destinations", tags=["destinations"])


async def _get_trip_for_user(db: AsyncSession, trip_id: int, user_id: int) -> Trip:
    res = await db.execute(select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id))
    trip = res.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.get(
    "",
    response_model=list[DestinationOut],
    summary="List destinations",
    description="List destinations. Optionally filter by trip_id.",
    operation_id="destinations_list",
)
async def list_destinations(
    trip_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DestinationOut]:
    """List destinations for current user, optionally for a specific trip."""
    stmt = select(Destination).join(Trip, Destination.trip_id == Trip.id).where(Trip.user_id == current_user.id)
    if trip_id is not None:
        stmt = stmt.where(Destination.trip_id == trip_id)
    res = await db.execute(stmt.order_by(Destination.id.desc()))
    return [DestinationOut.model_validate(d) for d in res.scalars().all()]


@router.post(
    "",
    response_model=DestinationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create destination",
    description="Create a destination under a trip (trip must belong to current user).",
    operation_id="destinations_create",
)
async def create_destination(
    payload: DestinationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DestinationOut:
    """Create a destination under a trip."""
    await _get_trip_for_user(db, payload.trip_id, current_user.id)

    dest = Destination(**payload.model_dump())
    db.add(dest)
    await db.commit()
    await db.refresh(dest)
    return DestinationOut.model_validate(dest)


@router.get(
    "/{destination_id}",
    response_model=DestinationOut,
    summary="Get destination",
    description="Get a destination (must belong to current user via its trip).",
    operation_id="destinations_get",
)
async def get_destination(
    destination_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DestinationOut:
    """Get destination by ID, scoped to current user."""
    stmt = (
        select(Destination)
        .join(Trip, Destination.trip_id == Trip.id)
        .where(Destination.id == destination_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")
    return DestinationOut.model_validate(dest)


@router.put(
    "/{destination_id}",
    response_model=DestinationOut,
    summary="Update destination",
    description="Update a destination (must belong to current user).",
    operation_id="destinations_update",
)
async def update_destination(
    destination_id: int,
    payload: DestinationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DestinationOut:
    """Update destination."""
    stmt = (
        select(Destination)
        .join(Trip, Destination.trip_id == Trip.id)
        .where(Destination.id == destination_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(dest, k, v)

    await db.commit()
    await db.refresh(dest)
    return DestinationOut.model_validate(dest)


@router.delete(
    "/{destination_id}",
    response_model=DeleteResponse,
    summary="Delete destination",
    description="Delete a destination (must belong to current user).",
    operation_id="destinations_delete",
)
async def delete_destination(
    destination_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DeleteResponse:
    """Delete destination."""
    stmt = (
        select(Destination)
        .join(Trip, Destination.trip_id == Trip.id)
        .where(Destination.id == destination_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    await db.delete(dest)
    await db.commit()
    return DeleteResponse(deleted=True)
