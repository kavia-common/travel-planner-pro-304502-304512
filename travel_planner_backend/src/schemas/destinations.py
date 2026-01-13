from pydantic import BaseModel, Field


class DestinationBase(BaseModel):
    trip_id: int = Field(..., description="Trip ID this destination belongs to")
    name: str = Field(..., min_length=1, max_length=200, description="Destination name")
    country: str | None = Field(default=None, max_length=100, description="Country")
    city: str | None = Field(default=None, max_length=100, description="City")
    lat: str | None = Field(default=None, max_length=50, description="Latitude (string for simplicity)")
    lng: str | None = Field(default=None, max_length=50, description="Longitude (string for simplicity)")
    notes: str | None = Field(default=None, description="Notes")


class DestinationCreate(DestinationBase):
    pass


class DestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200, description="Destination name")
    country: str | None = Field(default=None, max_length=100, description="Country")
    city: str | None = Field(default=None, max_length=100, description="City")
    lat: str | None = Field(default=None, max_length=50, description="Latitude")
    lng: str | None = Field(default=None, max_length=50, description="Longitude")
    notes: str | None = Field(default=None, description="Notes")


class DestinationOut(DestinationBase):
    id: int = Field(..., description="Destination ID")

    model_config = {"from_attributes": True}
