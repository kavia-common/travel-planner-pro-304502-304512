from datetime import datetime
from pydantic import BaseModel, Field


class ItineraryItemBase(BaseModel):
    trip_id: int = Field(..., description="Trip ID")
    destination_id: int | None = Field(default=None, description="Optional destination ID")
    title: str = Field(..., min_length=1, max_length=200, description="Title")
    description: str | None = Field(default=None, description="Description")
    start_time: datetime | None = Field(default=None, description="Start time (ISO)")
    end_time: datetime | None = Field(default=None, description="End time (ISO)")
    all_day: bool = Field(default=False, description="All-day event")


class ItineraryItemCreate(ItineraryItemBase):
    pass


class ItineraryItemUpdate(BaseModel):
    destination_id: int | None = Field(default=None, description="Optional destination ID")
    title: str | None = Field(default=None, min_length=1, max_length=200, description="Title")
    description: str | None = Field(default=None, description="Description")
    start_time: datetime | None = Field(default=None, description="Start time (ISO)")
    end_time: datetime | None = Field(default=None, description="End time (ISO)")
    all_day: bool | None = Field(default=None, description="All-day event")


class ItineraryItemOut(ItineraryItemBase):
    id: int = Field(..., description="Itinerary item ID")

    model_config = {"from_attributes": True}
