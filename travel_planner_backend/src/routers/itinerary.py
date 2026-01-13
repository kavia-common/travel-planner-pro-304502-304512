from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.common import DeleteResponse
from src.schemas.itinerary import ItineraryItemCreate, ItineraryItemOut, ItineraryItemUpdate
from src.storage.db import get_db_session
from src.storage.models import Destination, ItineraryItem, Trip, User

router = APIRouter(prefix="/itinerary", tags=["itinerary"])


async def _assert_trip_owned(db: AsyncSession, trip_id: int, user_id: int) -> None:
    res = await db.execute(select(Trip.id).where(Trip.id == trip_id, Trip.user_id == user_id))
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")


async def _assert_destination_in_trip(db: AsyncSession, destination_id: int, trip_id: int) -> None:
    res = await db.execute(select(Destination.id).where(Destination.id == destination_id, Destination.trip_id == trip_id))
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="destination_id not in trip")


@router.get(
    "",
    response_model=list[ItineraryItemOut],
    summary="List itinerary items",
    description="List itinerary items. Optionally filter by trip_id.",
    operation_id="itinerary_list",
)
async def list_itinerary_items(
    trip_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ItineraryItemOut]:
    """List itinerary items for current user."""
    stmt = select(ItineraryItem).join(Trip, ItineraryItem.trip_id == Trip.id).where(Trip.user_id == current_user.id)
    if trip_id is not None:
        stmt = stmt.where(ItineraryItem.trip_id == trip_id)
    res = await db.execute(stmt.order_by(ItineraryItem.id.desc()))
    return [ItineraryItemOut.model_validate(i) for i in res.scalars().all()]


@router.post(
    "",
    response_model=ItineraryItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create itinerary item",
    description="Create an itinerary item under a trip (trip must belong to current user).",
    operation_id="itinerary_create",
)
async def create_itinerary_item(
    payload: ItineraryItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ItineraryItemOut:
    """Create itinerary item."""
    await _assert_trip_owned(db, payload.trip_id, current_user.id)
    if payload.start_time and payload.end_time and payload.end_time < payload.start_time:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_time cannot be before start_time")
    if payload.destination_id is not None:
        await _assert_destination_in_trip(db, payload.destination_id, payload.trip_id)

    item = ItineraryItem(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ItineraryItemOut.model_validate(item)


@router.get(
    "/{item_id}",
    response_model=ItineraryItemOut,
    summary="Get itinerary item",
    description="Get an itinerary item (must belong to current user via its trip).",
    operation_id="itinerary_get",
)
async def get_itinerary_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ItineraryItemOut:
    """Get itinerary item."""
    stmt = (
        select(ItineraryItem)
        .join(Trip, ItineraryItem.trip_id == Trip.id)
        .where(ItineraryItem.id == item_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary item not found")
    return ItineraryItemOut.model_validate(item)


@router.put(
    "/{item_id}",
    response_model=ItineraryItemOut,
    summary="Update itinerary item",
    description="Update an itinerary item (must belong to current user).",
    operation_id="itinerary_update",
)
async def update_itinerary_item(
    item_id: int,
    payload: ItineraryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ItineraryItemOut:
    """Update itinerary item."""
    stmt = (
        select(ItineraryItem)
        .join(Trip, ItineraryItem.trip_id == Trip.id)
        .where(ItineraryItem.id == item_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary item not found")

    data = payload.model_dump(exclude_unset=True)
    if "start_time" in data or "end_time" in data:
        start = data.get("start_time", item.start_time)
        end = data.get("end_time", item.end_time)
        if start and end and end < start:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_time cannot be before start_time")

    if "destination_id" in data and data["destination_id"] is not None:
        await _assert_destination_in_trip(db, int(data["destination_id"]), item.trip_id)

    for k, v in data.items():
        setattr(item, k, v)

    await db.commit()
    await db.refresh(item)
    return ItineraryItemOut.model_validate(item)


@router.delete(
    "/{item_id}",
    response_model=DeleteResponse,
    summary="Delete itinerary item",
    description="Delete an itinerary item (must belong to current user).",
    operation_id="itinerary_delete",
)
async def delete_itinerary_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DeleteResponse:
    """Delete itinerary item."""
    stmt = (
        select(ItineraryItem)
        .join(Trip, ItineraryItem.trip_id == Trip.id)
        .where(ItineraryItem.id == item_id, Trip.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary item not found")

    await db.delete(item)
    await db.commit()
    return DeleteResponse(deleted=True)
