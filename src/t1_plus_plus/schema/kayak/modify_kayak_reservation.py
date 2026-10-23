from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ModifyKayakReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    booking_id: str = Field(..., description="The unique identifier for the existing kayak reservation.")
    new_date: Optional[str] = Field(default=None, description="The new date of the reservation in 'YYYY-MM-DD' format.")
    new_start_time: Optional[str] = Field(default=None, description="The new start time in 'HH:MM' format.")
    new_duration: Optional[int] = Field(default=None, description="The new duration of the rental in hours.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_duration")
    @classmethod
    def validate_duration(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("Rental duration must be at least 1 hour.")
        return value
        
    @field_validator("new_date")
    @classmethod
    def validate_date_format(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in 'YYYY-MM-DD' format.")
        return value

    @field_validator("new_start_time")
    @classmethod
    def validate_time_format(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            try:
                datetime.strptime(value, "%H:%M")
            except ValueError:
                raise ValueError("Time must be in 'HH:MM' (24-hour) format.")
        return value


class ModifyKayakReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the modification attempt.")
    message: str = Field(..., description="A descriptive message regarding the outcome.")
    booking_id: Optional[str] = Field(default=None, description="The ID of the modified booking.")
    updated_total_cost: Optional[float] = Field(default=None, description="The new total calculated cost, if duration was changed.")

    model_config = ConfigDict(extra="forbid")