from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookKayakReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user making the booking.")
    rental_id: str = Field(..., description="The unique identifier for the rental business.")
    vessel_type: str = Field(..., description="The specific craft being reserved.")
    date: str = Field(..., description="The date of the reservation in 'YYYY-MM-DD' format.")
    start_time: str = Field(..., description="The start time of the reservation in 'HH:MM' format.")
    duration: int = Field(..., description="The duration of the rental in hours.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Rental duration must be at least 1 hour.")
        return value
        
    @field_validator("date")
    @classmethod
    def validate_date_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Date must be in 'YYYY-MM-DD' format.")

    @field_validator("start_time")
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            raise ValueError("Time must be in 'HH:MM' (24-hour) format.")


class BookKayakReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the booking attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the booking outcome.")
    booking_id: Optional[str] = Field(default=None, description="The unique identifier for the new reservation.")
    total_cost: Optional[float] = Field(default=None, description="The final calculated total cost for the reservation.")
    
    model_config = ConfigDict(extra="forbid")