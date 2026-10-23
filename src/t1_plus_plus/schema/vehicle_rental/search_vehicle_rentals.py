from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchRentalsInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a rental at. This is required.",
    )
    make: Optional[List[str]] = Field(default=None)
    model: Optional[List[str]] = Field(default=None)
    vehicle_id: Optional[List[str]] = Field(default=None)
    year: Optional[List[int]] = Field(default=None, description="Range: 2015-2025.")
    category: Optional[str] = Field(default=None, description="car, bike, or truck.")
    subcategory: Optional[str] = Field(default=None)
    price_tier: Optional[str] = Field(
        default=None, description="luxury, premium, classic, or budget."
    )

    # Status & Specs
    odometer: Optional[int] = Field(default=None, description="0-200,000.")
    seats: Optional[int] = Field(default=None)
    fuel_type: Optional[str] = Field(default=None)
    rating: Optional[List[float]] = Field(default=None, description="[min, max]")
    base_price_per_day: Optional[float] = Field(default=None, description="Max budget.")

    # Features (from RENTAL_FEATURES)
    has_gps: Optional[bool] = Field(default=None)
    is_automatic: Optional[bool] = Field(default=None)
    has_unlimited_mileage: Optional[bool] = Field(default=None)
    is_pet_friendly: Optional[bool] = Field(default=None)
    has_insurance_included: Optional[bool] = Field(default=None)
    has_child_seat_option: Optional[bool] = Field(default=None)
    has_tow_hitch: Optional[bool] = Field(default=None)
    is_wheelchair_accessible: Optional[bool] = Field(default=None)

    model_config = ConfigDict(extra="forbid")

    @field_validator("rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> Optional[List[float]]:
        if value is None:
            return value
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("Rating must be a list of [min, max].")
        return [float(v) for v in value]
