from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import get_current_user
from src.schemas.bookings import BookingCreate, BookingOut, BookingUpdate
from src.schemas.common import DeleteResponse
from src.storage.db import get_db_session
from src.storage.models import Booking, Trip, User

router = APIRouter(prefix="/bookings", tags=["bookings"])


async def _assert_trip_owned(db: AsyncSession, trip_id: int, user_id: int) -> None:
    res = await db.execute(select(Trip.id).where(Trip.id == trip_id, Trip.user_id == user_id))
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")


@router.get(
    "",
    response_model=list[BookingOut],
    summary="List bookings",
    description="List bookings. Optionally filter by trip_id.",
    operation_id="bookings_list",
)
async def list_bookings(
    trip_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[BookingOut]:
    """List bookings for current user."""
    stmt = select(Booking).join(Trip, Booking.trip_id == Trip.id).where(Trip.user_id == current_user.id)
    if trip_id is not None:
        stmt = stmt.where(Booking.trip_id == trip_id)
    res = await db.execute(stmt.order_by(Booking.created_at.desc()))
    return [BookingOut.model_validate(b) for b in res.scalars().all()]


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create booking",
    description="Create a booking under a trip (trip must belong to current user).",
    operation_id="bookings_create",
)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> BookingOut:
    """Create booking."""
    await _assert_trip_owned(db, payload.trip_id, current_user.id)
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date cannot be before start_date")

    booking = Booking(**payload.model_dump())
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return BookingOut.model_validate(booking)


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Get booking",
    description="Get a booking (must belong to current user via its trip).",
    operation_id="bookings_get",
)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> BookingOut:
    """Get booking."""
    stmt = select(Booking).join(Trip, Booking.trip_id == Trip.id).where(Booking.id == booking_id, Trip.user_id == current_user.id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return BookingOut.model_validate(booking)


@router.put(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Update booking",
    description="Update a booking (must belong to current user).",
    operation_id="bookings_update",
)
async def update_booking(
    booking_id: int,
    payload: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> BookingOut:
    """Update booking."""
    stmt = select(Booking).join(Trip, Booking.trip_id == Trip.id).where(Booking.id == booking_id, Trip.user_id == current_user.id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    data = payload.model_dump(exclude_unset=True)
    if "start_date" in data or "end_date" in data:
        start = data.get("start_date", booking.start_date)
        end = data.get("end_date", booking.end_date)
        if start and end and end < start:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date cannot be before start_date")

    for k, v in data.items():
        setattr(booking, k, v)

    await db.commit()
    await db.refresh(booking)
    return BookingOut.model_validate(booking)


@router.delete(
    "/{booking_id}",
    response_model=DeleteResponse,
    summary="Delete booking",
    description="Delete a booking (must belong to current user).",
    operation_id="bookings_delete",
)
async def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DeleteResponse:
    """Delete booking."""
    stmt = select(Booking).join(Trip, Booking.trip_id == Trip.id).where(Booking.id == booking_id, Trip.user_id == current_user.id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    await db.delete(booking)
    await db.commit()
    return DeleteResponse(deleted=True)
