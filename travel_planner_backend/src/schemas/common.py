from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str = Field(..., description="Human-readable message")


class DeleteResponse(BaseModel):
    """Standard delete response."""
    deleted: bool = Field(..., description="Whether the record was deleted")
