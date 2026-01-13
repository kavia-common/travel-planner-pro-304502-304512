from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.common import DeleteResponse
from src.schemas.trips import TripCreate, TripOut, TripUpdate
from src.storage.db import get_db_session
from src.storage.models import Trip, User

router = APIRouter(prefix="/trips", tags=["trips"])


async def _ensure_demo_trip(db: AsyncSession, user: User) -> None:
    """Seed a demo trip for the first user if none exist."""
    res = await db.execute(select(Trip).where(Trip.user_id == user.id).limit(1))
    if res.scalar_one_or_none():
        return
    demo_trip = Trip(
        user_id=user.id,
        name="Weekend in Paris",
        description="A quick demo trip with a few sample items.",
    )
    db.add(demo_trip)
    await db.commit()


@router.get(
    "",
    response_model=list[TripOut],
    summary="List trips",
    description="List trips belonging to the current user.",
    operation_id="trips_list",
)
async def list_trips(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TripOut]:
    """List trips for the authenticated user."""
    await _ensure_demo_trip(db, current_user)
    res = await db.execute(select(Trip).where(Trip.user_id == current_user.id).order_by(Trip.created_at.desc()))
    return [TripOut.model_validate(t) for t in res.scalars().all()]


@router.post(
    "",
    response_model=TripOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create trip",
    description="Create a new trip for the current user.",
    operation_id="trips_create",
)
async def create_trip(
    payload: TripCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TripOut:
    """Create a trip for the authenticated user."""
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date cannot be before start_date")

    trip = Trip(user_id=current_user.id, **payload.model_dump())
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    return TripOut.model_validate(trip)


@router.get(
    "/{trip_id}",
    response_model=TripOut,
    summary="Get trip",
    description="Get a single trip by ID (must belong to current user).",
    operation_id="trips_get",
)
async def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TripOut:
    """Get a trip by ID scoped to current user."""
    res = await db.execute(select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id))
    trip = res.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return TripOut.model_validate(trip)


@router.put(
    "/{trip_id}",
    response_model=TripOut,
    summary="Update trip",
    description="Update a trip by ID (must belong to current user).",
    operation_id="trips_update",
)
async def update_trip(
    trip_id: int,
    payload: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TripOut:
    """Update trip details."""
    res = await db.execute(select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id))
    trip = res.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    data = payload.model_dump(exclude_unset=True)
    if "start_date" in data or "end_date" in data:
        start = data.get("start_date", trip.start_date)
        end = data.get("end_date", trip.end_date)
        if start and end and end < start:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date cannot be before start_date")

    for k, v in data.items():
        setattr(trip, k, v)

    await db.commit()
    await db.refresh(trip)
    return TripOut.model_validate(trip)


@router.delete(
    "/{trip_id}",
    response_model=DeleteResponse,
    summary="Delete trip",
    description="Delete a trip and all nested resources (destinations, itinerary items, bookings).",
    operation_id="trips_delete",
)
async def delete_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DeleteResponse:
    """Delete a trip by ID."""
    res = await db.execute(select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id))
    trip = res.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    await db.delete(trip)
    await db.commit()
    return DeleteResponse(deleted=True)
