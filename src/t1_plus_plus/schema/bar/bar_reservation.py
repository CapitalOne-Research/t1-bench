from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BarReservation(BaseModel):
    """Represents a booked reservation."""

    reservation_id: str = Field(..., description="Unique ID for the reservation")
    user_id: str
    venue_id: str
    primary_guest_name: str
    number_guests: int
    event_datetime: datetime
    credit_card_last_four: str
    is_vip_room: bool = False
    reservation_charge: float
    latest_refund_date_days: int
    status: str


class BookBarReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    venue_id: str = Field(..., description="The unique identifier for the bar/venue.")
    event_datetime: str = Field(
        ...,
        description="The date and time of the reservation in YYYY-MM-DD HH:MM format.",
    )
    number_guests: int = Field(
        ..., description="Total number of guests, including the primary guest."
    )
    primary_guest_name: str = Field(
        ..., description="First and last name of the primary guest."
    )
    credit_card_last_four: str = Field(
        ..., description="The last four digits of the credit card used for booking."
    )
    has_drivers_license: bool = Field(
        ...,
        description="Whether the primary guest has a valid driver's license checked by the agent.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("event_datetime", mode="before")
    @classmethod
    def validate_datetime(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M")
            return value
        except ValueError:
            raise ValueError("event_datetime must be in 'YYYY-MM-DD HH:MM' format.")


class ModifyBarReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    new_event_datetime: Optional[str] = Field(
        default=None,
        description="The new date and time for the reservation in YYYY-MM-DD HH:MM format.",
    )
    new_number_guests: Optional[int] = Field(
        default=None, description="The updated number of guests."
    )
    upgrade_vip_room: Optional[bool] = Field(
        default=None,
        description="Set to True if the user wants to upgrade to a VIP private room.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_event_datetime", mode="before")
    @classmethod
    def validate_new_datetime(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M")
            return value
        except ValueError:
            raise ValueError("new_event_datetime must be in 'YYYY-MM-DD HH:MM' format.")


class CancelBarReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    reason: str = Field(
        ..., description="The user's provided reason for cancelling the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class BookBarReservationOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the booking attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message for the user regarding the booking outcome.",
    )
    reservation_id: Optional[str] = Field(
        default=None,
        description="The unique identifier for the newly created reservation.",
    )
    reservation_charge: Optional[float] = Field(
        default=None, description="The total charge applied for the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class ModifyBarReservationOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the modification attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message for the user regarding the modification outcome.",
    )
    reservation_id: Optional[str] = Field(
        default=None, description="The unique identifier for the modified reservation."
    )
    new_charge: Optional[float] = Field(
        default=None,
        description="The updated total charge for the reservation, if applicable.",
    )
    is_vip: Optional[bool] = Field(
        default=None,
        description="Indicates whether the reservation now includes a VIP room upgrade.",
    )

    model_config = ConfigDict(extra="forbid")


class CancelBarReservationOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the cancellation attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message for the user regarding the cancellation outcome.",
    )
    refund_status: Optional[str] = Field(
        default=None,
        description="Indicates the refund outcome (e.g., 'Full Refund' or 'Late Cancellation Fee Applied').",
    )
    fee_charged: Optional[float] = Field(
        default=None,
        description="The amount charged if the cancellation was made within the late cancellation window.",
    )
    reason_logged: Optional[str] = Field(
        default=None, description="The cancellation reason provided by the user."
    )

    model_config = ConfigDict(extra="forbid")
