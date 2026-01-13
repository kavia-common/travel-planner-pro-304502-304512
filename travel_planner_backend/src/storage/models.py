from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    trips: Mapped[list["Trip"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="trips")
    destinations: Mapped[list["Destination"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    itinerary_items: Mapped[list["ItineraryItem"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lat: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lng: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trip: Mapped["Trip"] = relationship(back_populates="destinations")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="destination", cascade="all, delete-orphan")


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False)
    destination_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("destinations.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    trip: Mapped["Trip"] = relationship(back_populates="itinerary_items")
    destination: Mapped[Optional["Destination"]] = relationship()


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False)

    booking_type: Mapped[str] = mapped_column(String(50), nullable=False)  # flight/hotel/car/activity/other
    provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    cost_amount: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    trip: Mapped["Trip"] = relationship(back_populates="bookings")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "destination_id", name="uq_favorites_user_destination"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="favorites")
    destination: Mapped["Destination"] = relationship(back_populates="favorites")
