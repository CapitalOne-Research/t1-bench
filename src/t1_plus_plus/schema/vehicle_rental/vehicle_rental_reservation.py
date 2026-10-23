from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RentalReservation(BaseModel):
    """Represents a booked vehicle rental in the database."""

    reservation_id: str = Field(..., description="Unique ID for the rental reservation")
    user_id: str
    vehicle_id: str
    primary_driver_name: str
    start_date: datetime
    end_date: datetime
    # Pricing & Metadata
    reservation_charge: float
    latest_refund_date_days: int = 1  # 24-hour refund policy
    status: str = "Active"

    # Captured Attributes from Dataset
    service_provider: str
    make: str
    model: str
    category: str
    base_price_per_day: float


class BookRentalReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    vehicle_id: str = Field(
        ..., description="The unique identifier (id) for the rental vehicle."
    )
    start_date: str = Field(
        ...,
        description="The start date of the rental in YYYY-MM-DD format.",
    )
    end_date: str = Field(
        ...,
        description="The end date of the rental in YYYY-MM-DD format.",
    )
    primary_driver_name: str = Field(
        ..., description="First and last name of the primary driver."
    )
    has_drivers_license: bool = Field(
        ...,
        description="Whether the primary driver has a valid driver's license checked by the agent.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")


class ModifyRentalReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    new_start_date: Optional[str] = Field(
        default=None,
        description="The new start date for the rental in YYYY-MM-DD format.",
    )
    new_end_date: Optional[str] = Field(
        default=None,
        description="The new end date for the rental in YYYY-MM-DD format.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_start_date", "new_end_date", mode="before")
    @classmethod
    def validate_new_date(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")


class CancelRentalReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(
        ..., description="The unique identifier for the existing reservation."
    )
    reason: str = Field(
        default="No reason provided",
        description="The user's provided reason for cancelling the reservation.",
    )

    model_config = ConfigDict(extra="forbid")


class BookRentalReservationOutputModel(BaseModel):
    status: str = Field(..., description="Status: 'success' or 'error'.")
    message: str = Field(..., description="Detailed outcome message.")
    reservation_id: Optional[str] = Field(default=None)
    reservation_charge: Optional[float] = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class ModifyRentalReservationOutputModel(BaseModel):
    status: str = Field(..., description="Status: 'success' or 'error'.")
    message: str = Field(..., description="Detailed outcome message.")
    reservation_id: Optional[str] = Field(default=None)
    new_charge: Optional[float] = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class CancelRentalReservationOutputModel(BaseModel):
    status: str = Field(..., description="Status: 'success' or 'error'.")
    message: str = Field(..., description="Detailed outcome message.")
    refund_status: Optional[str] = Field(default=None)
    fee_charged: Optional[float] = Field(default=None)
    reason_logged: Optional[str] = Field(default=None)

    model_config = ConfigDict(extra="forbid")
