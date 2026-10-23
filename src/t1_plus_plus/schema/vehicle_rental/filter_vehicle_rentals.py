from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FilterRentalsInputModel(BaseModel):
    cache_key: str = Field(
        ...,
        description="The cache key used to retrieve prior rental search results. Use 'search_vehicle_rentals_results_0' for the first search, 'search_vehicle_rentals_results_1' for a second search (compare scenario). Do NOT use 'prior_results'.",
    )
    # city is optional here as it is inherited from prior_results
    city: Optional[str] = Field(default=None)
    make: Optional[List[str]] = Field(default=None)
    model: Optional[List[str]] = Field(default=None)
    year: Optional[List[int]] = Field(default=None)
    category: Optional[str] = Field(default=None)
    price_tier: Optional[str] = Field(default=None)
    rating: Optional[List[float]] = Field(default=None)
    base_price_per_day: Optional[float] = Field(default=None)

    # Status & Specs
    odometer: Optional[int] = Field(default=None, description="0-200,000.")
    seats: Optional[int] = Field(default=None)
    fuel_type: Optional[str] = Field(default=None)
    rating: Optional[List[float]] = Field(default=None, description="[min, max]")

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
        return [float(v) for v in value]
