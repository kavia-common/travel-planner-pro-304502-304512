from datetime import date, datetime
from pydantic import BaseModel, Field


class BookingBase(BaseModel):
    trip_id: int = Field(..., description="Trip ID")
    booking_type: str = Field(..., min_length=1, max_length=50, description="Type: flight/hotel/car/activity/other")
    provider: str | None = Field(default=None, max_length=200, description="Provider (airline/hotel/etc)")
    reference: str | None = Field(default=None, max_length=200, description="Confirmation/reference number")
    start_date: date | None = Field(default=None, description="Start date")
    end_date: date | None = Field(default=None, description="End date")
    cost_amount: str | None = Field(default=None, max_length=50, description="Cost amount (string for simplicity)")
    cost_currency: str | None = Field(default=None, max_length=10, description="Currency code")
    notes: str | None = Field(default=None, description="Notes")


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    booking_type: str | None = Field(default=None, min_length=1, max_length=50, description="Type")
    provider: str | None = Field(default=None, max_length=200, description="Provider")
    reference: str | None = Field(default=None, max_length=200, description="Reference")
    start_date: date | None = Field(default=None, description="Start date")
    end_date: date | None = Field(default=None, description="End date")
    cost_amount: str | None = Field(default=None, max_length=50, description="Cost amount")
    cost_currency: str | None = Field(default=None, max_length=10, description="Currency")
    notes: str | None = Field(default=None, description="Notes")


class BookingOut(BookingBase):
    id: int = Field(..., description="Booking ID")
    created_at: datetime = Field(..., description="Created timestamp")

    model_config = {"from_attributes": True}
