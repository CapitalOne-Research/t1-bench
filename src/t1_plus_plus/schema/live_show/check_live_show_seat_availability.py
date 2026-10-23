from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CheckSeatAvailabilityInputModel(BaseModel):
    live_event_id: str = Field(..., description="The unique live event ID (e.g., 'LE0').")
    seat_location: Optional[List[str]] = Field(default=None, description="Seat section(s) to check (e.g., ['front', 'middle']). If omitted, checks all sections.")
    number_tickets: int = Field(..., description="Number of tickets the user wants to book.")

    model_config = ConfigDict(extra="forbid")


class CheckSeatAvailabilityOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="A message describing the result.")
    sections: Optional[dict] = Field(default=None, description="Availability details per section. Each section has: available (bool), seats_remaining (int).")

    model_config = ConfigDict(extra="forbid")
