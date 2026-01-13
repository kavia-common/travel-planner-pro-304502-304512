from datetime import datetime
from pydantic import BaseModel, Field


class FavoriteCreate(BaseModel):
    destination_id: int = Field(..., description="Destination to favorite")


class FavoriteOut(BaseModel):
    id: int = Field(..., description="Favorite ID")
    user_id: int = Field(..., description="User ID")
    destination_id: int = Field(..., description="Destination ID")
    created_at: datetime = Field(..., description="Created timestamp")

    model_config = {"from_attributes": True}
