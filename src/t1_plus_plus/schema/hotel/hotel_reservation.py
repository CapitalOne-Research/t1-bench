from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HotelReservation(BaseModel):
    """Represents a booked hotel reservation in the database."""

    reservation_id: str = Field(..., description="Unique ID for the reservation")
    user_id: str
    hotel_id: str
    room_id: str
    check_in_date: str
    check_out_date: str
    payment_method: str
    total: float
    status: str


# ==========================================
# GET RESERVATION SCHEMAS
# ==========================================

class GetHotelReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: Optional[str] = Field(
        default=None, 
        description="The unique identifier for the existing reservation (optional)."
    )

    model_config = ConfigDict(extra="forbid")


class GetHotelReservationOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the retrieval attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message regarding the retrieval outcome.",
    )
    reservations: Optional[List[HotelReservation]] = Field(
        default=None,
        description="A list of reservation objects belonging to the user."
    )

    model_config = ConfigDict(extra="forbid")


# ==========================================
# BOOK RESERVATION SCHEMAS
# ==========================================

class BookHotelReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    hotel_id: str = Field(..., description="The unique identifier for the hotel.")
    room_id: str = Field(..., description="The unique identifier for the specific room.")
    check_in_date: str = Field(
        ...,
        description="The check-in date in YYYY-MM-DD format.",
    )
    check_out_date: str = Field(
        ...,
        description="The check-out date in YYYY-MM-DD format.",
    )
    payment_method: str = Field(
        ..., 
        description="The single payment method chosen by the user (e.g., 'credit_card' or 'reward_points')."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("check_in_date", "check_out_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")


class BookHotelReservationOutputModel(BaseModel):
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
    total_charged: Optional[float] = Field(
        default=None, 
        description="The total amount charged for the reservation."
    )
    currency_type: Optional[str] = Field(
        default=None,
        description="Indicates if the total was charged in 'cash' or 'points'."
    )

    model_config = ConfigDict(extra="forbid")


# ==========================================
# CANCEL RESERVATION SCHEMAS
# ==========================================

class CancelHotelReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )

    model_config = ConfigDict(extra="forbid")


class CancelHotelReservationOutputModel(BaseModel):
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
        description="The amount charged (usually one night's stay) if cancelled within 48 hours, or 100% for non-refundable.",
    )

    model_config = ConfigDict(extra="forbid")


# ==========================================
# MODIFY RESERVATION SCHEMAS
# ==========================================

class ModifyHotelReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    new_check_in_date: Optional[str] = Field(
        default=None,
        description="The new check-in date in YYYY-MM-DD format.",
    )
    new_check_out_date: Optional[str] = Field(
        default=None,
        description="The new check-out date in YYYY-MM-DD format.",
    )
    new_room_id: Optional[str] = Field(
        default=None,
        description="The new room ID to switch to (must belong to the same hotel).",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_check_in_date", "new_check_out_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")


class ModifyHotelReservationOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the modification attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message for the user regarding the modification outcome.",
    )
    reservation_id: Optional[str] = Field(
        default=None,
        description="The unique identifier for the modified reservation.",
    )
    new_total: Optional[float] = Field(
        default=None,
        description="The updated total charge for the reservation.",
    )
    currency_type: Optional[str] = Field(
        default=None,
        description="Indicates if the total is in 'cash' or 'points'.",
    )

    model_config = ConfigDict(extra="forbid")


# ==========================================
# GET ROOM INVENTORY SCHEMAS
# ==========================================

class HotelRoomItem(BaseModel):
    """Represents a single room's details in the hotel's inventory."""
    room_id: str = Field(..., description="The unique identifier for the room.")
    room_type: str = Field(..., description="Type of room (e.g., 'One King', 'Suite').")
    view_type: str = Field(..., description="The type of view from the room.")
    occupancy: int = Field(..., description="The maximum guest occupancy for the room.")
    cash_price: float = Field(..., description="The nightly cash price of the room.")
    points_price: int = Field(..., description="The nightly reward points price of the room.")
    resort_fees: float = Field(..., description="The nightly resort fees applied to the room.")
    price_tier: str = Field(..., description="The cancellation policy price tier ($, $$, or $$$).")
    status: str = Field(..., description="The current status of the room (e.g., 'Available').")


class GetHotelRoomInventoryInputModel(BaseModel):
    hotel_id: str = Field(..., description="The unique identifier for the hotel.")
    check_in_date: str = Field(
        ...,
        description="The requested check-in date in YYYY-MM-DD format.",
    )
    check_out_date: str = Field(
        ...,
        description="The requested check-out date in YYYY-MM-DD format.",
    )
    occupancy: int = Field(
        ..., 
        description="The required minimum guest occupancy."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("check_in_date", "check_out_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")


class GetHotelRoomInventoryOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the retrieval attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message regarding the retrieval outcome.",
    )
    hotel_name: Optional[str] = Field(
        default=None,
        description="The name of the hotel being queried.",
    )
    rooms: Optional[List[HotelRoomItem]] = Field(
        default=None,
        description="A list of room objects that are available and meet the requested criteria."
    )

    model_config = ConfigDict(extra="forbid")