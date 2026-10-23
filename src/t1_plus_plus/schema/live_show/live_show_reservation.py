from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShowReservation(BaseModel):
    """Represents a booked show reservation."""

    reservation_id: str = Field(..., description="Unique ID for the reservation")
    user_id: str
    venue_id: str
    show_name: str
    event_datetime: datetime
    seat_location: str
    number_tickets: int
    primary_guest_name: str
    total_price: float
    credit_card_last_four: str
    latest_refund_date_days: int
    status: str


class BookLiveShowReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The ID of the user making the booking.")
    live_event_id: str = Field(..., description="The unique live event ID (e.g., 'LE0').")
    seat_location: Literal["front", "middle", "back"] = Field(
        ..., description="The section to book seats in."
    )
    number_tickets: int = Field(..., description="Number of tickets to reserve.")
    primary_guest_name: str = Field(..., description="Full name of the primary guest.")
    credit_card_last_four: str = Field(
        ..., description="Last four digits of the credit card for payment."
    )

    model_config = ConfigDict(extra="forbid")


class ModifyLiveShowReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    new_seat_location: Optional[Literal["front", "middle", "back"]] = Field(
        default=None, description="The new section to move seats to."
    )
    new_number_tickets: Optional[int] = Field(
        default=None, description="The updated number of tickets."
    )

    model_config = ConfigDict(extra="forbid")


class CancelLiveShowReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    reason: str = Field(
        ..., description="The user's provided reason for cancelling the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class BookLiveShowReservationOutputModel(BaseModel):
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
    total_price: Optional[float] = Field(
        default=None, description="The total charge applied for the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class ModifyLiveShowReservationOutputModel(BaseModel):
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
    new_total_price: Optional[float] = Field(
        default=None,
        description="The updated total charge for the reservation, if applicable.",
    )

    model_config = ConfigDict(extra="forbid")


class CancelLiveShowReservationOutputModel(BaseModel):
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
        description="Indicates the refund outcome (e.g., 'Full Refund' or 'Cancellation Fee Applied').",
    )
    fee_charged: Optional[float] = Field(
        default=None,
        description="The amount charged if the cancellation was made late.",
    )

    model_config = ConfigDict(extra="forbid")


