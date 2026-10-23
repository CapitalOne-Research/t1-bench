from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FlightReservation(BaseModel):
    """Represents a booked flight reservation."""

    reservation_id: str = Field(..., description="Unique ID for the reservation")
    user_id: str
    flight_id: str
    passenger_names: List[str]
    number_passengers: int
    departure_date: datetime
    departure_city: Optional[str] = Field(default=None, description="The departure city name.")
    arrival_city: Optional[str] = Field(default=None, description="The arrival city name.")
    ticket_class: Optional[str] = Field(default=None, description="The ticket class (e.g., 'Economy', 'Business', 'First').")
    credit_card_last_four: str
    reservation_charge: float
    latest_refund_date_days: int
    status: str


class BookFlightReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    flight_id: str = Field(..., description="The unique identifier for the flight.")
    passenger_names: List[str] = Field(
        ..., description="List of first and last names for each passenger."
    )
    number_passengers: int = Field(
        ..., description="Total number of passengers."
    )
    credit_card_last_four: str = Field(
        ..., description="The last four digits of the credit card used for booking."
    )
    departure_city: Optional[str] = Field(
        default=None, description="The departure city name (e.g., 'Los Angeles')."
    )
    arrival_city: Optional[str] = Field(
        default=None, description="The arrival city name (e.g., 'New York')."
    )
    departure_date: Optional[str] = Field(
        default=None,
        description="The departure date in YYYY-MM-DD format.",
    )
    ticket_class: Optional[str] = Field(
        default=None, description="The ticket class (e.g., 'Economy', 'Business', 'First')."
    )

    model_config = ConfigDict(extra="forbid")


class CancelFlightReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    reason: str = Field(
        ..., description="The user's provided reason for cancelling the reservation."
    )

    model_config = ConfigDict(extra="forbid")


class BookFlightReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the booking attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    reservation_id: Optional[str] = Field(default=None, description="The unique identifier for the newly created reservation.")
    reservation_charge: Optional[float] = Field(default=None, description="The total charge applied.")
    model_config = ConfigDict(extra="forbid")


class CancelFlightReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the cancellation attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    refund_status: Optional[str] = Field(default=None, description="Indicates the refund outcome (e.g., 'Full Refund' or 'Late Cancellation Fee Applied').")
    fee_charged: Optional[float] = Field(default=None, description="The amount charged if the cancellation was made within the late cancellation window.")
    reason_logged: Optional[str] = Field(default=None, description="The cancellation reason provided by the user.")
    model_config = ConfigDict(extra="forbid")


class GetFlightReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: Optional[str] = Field(
        default=None,
        description="The unique identifier for the existing reservation (optional). If omitted, all reservations for the user are returned.",
    )

    model_config = ConfigDict(extra="forbid")


class GetFlightReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the retrieval attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    reservations: Optional[List[FlightReservation]] = Field(
        default=None, description="A list of flight reservations belonging to the user."
    )
    model_config = ConfigDict(extra="forbid")


class ModifyFlightReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(..., description="The unique identifier for the existing reservation.")
    new_departure_date: Optional[str] = Field(
        default=None,
        description="The new departure date in YYYY-MM-DD format.",
    )
    new_number_passengers: Optional[int] = Field(
        default=None, description="The updated number of passengers."
    )
    departure_city: Optional[str] = Field(
        default=None, description="The updated departure city name."
    )
    arrival_city: Optional[str] = Field(
        default=None, description="The updated arrival city name."
    )
    passenger_names: Optional[List[str]] = Field(
        default=None, description="The updated list of passenger names."
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


class ModifyFlightReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the modification attempt ('success' or 'error').")
    message: str = Field(..., description="A descriptive message for the user.")
    reservation_id: Optional[str] = Field(default=None, description="The unique identifier for the modified reservation.")
    new_charge: Optional[float] = Field(default=None, description="The updated total charge for the reservation.")
    model_config = ConfigDict(extra="forbid")
