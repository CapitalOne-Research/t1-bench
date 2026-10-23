from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class GetShowDetailsInputModel(BaseModel):
    live_event_id: Optional[str] = Field(default=None, description="The unique live event ID (e.g., 'LE0'). If provided, venue_id and show_name are not required.")
    venue_id: Optional[str] = Field(default=None, description="The unique ID of the venue where the show is held.")
    show_name: Optional[str] = Field(default=None, description="The name of the show to retrieve details for.")

    model_config = ConfigDict(extra="forbid")

class GetShowDetailsOutputModel(BaseModel):
    status: str = Field(..., description="Status of the lookup (success or error).")
    message: str = Field(..., description="A message describing the result.")
    details: Optional[Dict[str, Any]] = Field(default=None, description="The detailed show information.")

    model_config = ConfigDict(extra="forbid")