from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FilterKayakRentalsInputModel(BaseModel):
    cache_key: str = Field(
        ...,
        description="The cache key used to retrieve prior kayak rental search results (e.g., 'previous_kayak_rentals').",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of specific neighborhoods or local areas within the city."
    )
    vessel_type: Optional[List[str]] = Field(
        default=None,
        description="List of watercraft available for rent (e.g., 'SUP', 'Tandem')."
    )
    business_name: Optional[List[str]] = Field(
        default=None,
        description="List of rental shop names."
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating."
    )
    price_per_hour: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum cost in USD for a one-hour rental."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("rating", "price_per_hour", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> List[float]:
        if not type(value) is list:
            raise ValueError("Value must be a list.")
        if len(value) != 2:
            raise ValueError("List must contain exactly two items: [minimum, maximum].")
        result = []
        for v in value:
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                raise ValueError("Each item in the list must be either an integer or a float.")
        return result