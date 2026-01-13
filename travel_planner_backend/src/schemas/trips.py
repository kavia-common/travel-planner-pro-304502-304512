from datetime import date, datetime
from pydantic import BaseModel, Field


class TripBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Trip name")
    description: str | None = Field(default=None, description="Trip description")
    start_date: date | None = Field(default=None, description="Trip start date")
    end_date: date | None = Field(default=None, description="Trip end date")


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200, description="Trip name")
    description: str | None = Field(default=None, description="Trip description")
    start_date: date | None = Field(default=None, description="Trip start date")
    end_date: date | None = Field(default=None, description="Trip end date")


class TripOut(TripBase):
    id: int = Field(..., description="Trip ID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Created timestamp")

    model_config = {"from_attributes": True}
