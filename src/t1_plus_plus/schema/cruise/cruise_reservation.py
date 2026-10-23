from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CruiseReservation(BaseModel):
    """Represents a booked cruise reservation."""

    reservation_id: str = Field(..., description="Unique ID for the reservation")
    user_id: str
    cruise_id: str
    primary_guest_name: str
    number_guests: int
    departure_date: datetime
    cabin_type: str
    credit_card_last_four: str
    is_upgraded: bool = False
    reservation_charge: float
    latest_refund_date_days: int
    status: str


class BookCruiseReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    cruise_id: str = Field(..., description="The unique identifier for the cruise.")
    departure_date: str = Field(
        ...,
        description="The departure date of the cruise in YYYY-MM-DD format.",
    )
    number_guests: int = Field(
        ..., description="Total number of guests, including the primary guest."
    )
    primary_guest_name: str = Field(
        ..., description="First and last name of the primary guest."
    )
    cabin_type: str = Field(
        ..., description="The type of cabin (e.g., interior, balcony, suite)."
    )
    credit_card_last_four: str = Field(
        ..., description="The last four digits of the credit card used for booking."
    )
    has_passport: bool = Field(
        ...,
        description="Whether the primary guest has a valid passport checked by the agent.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("departure_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("departure_date must be in 'YYYY-MM-DD' format.")


class ModifyCruiseReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    new_departure_date: Optional[str] = Field(
        default=None,
        description="The new departure date for the reservation in YYYY-MM-DD format.",
    )
    new_number_guests: Optional[int] = Field(
        default=None, description="The updated number of guests."
    )
    upgrade_cabin: Optional[bool] = Field(
        default=None,
        description="Set to True if the user wants to upgrade their cabin to a Suite.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_departure_date", mode="before")
    @classmethod
    def validate_new_date(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("new_departure_date must be in 'YYYY-MM-DD' format.")


class CancelCruiseReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    reason: str = Field(
        ..., description="The user's provided reason for cancelling the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class BookCruiseReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the booking attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    reservation_id: Optional[str] = Field(default=None, description="The unique identifier for the newly created reservation.")
    reservation_charge: Optional[float] = Field(default=None, description="The total charge applied.")
    model_config = ConfigDict(extra="forbid")


class ModifyCruiseReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the modification attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    reservation_id: Optional[str] = Field(default=None, description="The unique identifier for the modified reservation.")
    new_charge: Optional[float] = Field(default=None, description="The updated total charge for the reservation, if applicable.")
    is_upgraded: Optional[bool] = Field(default=None, description="Indicates whether the reservation now includes a cabin upgrade.")
    model_config = ConfigDict(extra="forbid")


class CancelCruiseReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the cancellation attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    refund_status: Optional[str] = Field(default=None, description="Indicates the refund outcome (e.g., 'Full Refund' or 'Late Cancellation Fee Applied').")
    fee_charged: Optional[float] = Field(default=None, description="The amount charged if the cancellation was made within the late cancellation window.")
    reason_logged: Optional[str] = Field(default=None, description="The cancellation reason provided by the user.")
    model_config = ConfigDict(extra="forbid")
