from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchKayakRentalsInputModel(BaseModel):
    city: Optional[str] = Field(
        default=None,
        description="The city where the user is looking for a kayak rental."
    )
    state: Optional[str] = Field(
        default=None,
        description="The two-letter state code where the user is looking for a rental."
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of specific neighborhoods or local areas within the city."
    )
    vessel_type: Optional[List[str]] = Field(
        default=None,
        description="List of watercraft available for rent. Allowed values: 'Single (Sit-on-Top)', 'Single (Sit-In)', 'Tandem', 'Fishing Kayak', 'SUP', 'Canoe'."
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating the user is willing to consider (1.0 to 5.0)."
    )
    price_per_hour: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum cost in USD for a one-hour rental."
    )
    business_name: Optional[List[str]] = Field(
        default=None,
        description="List of rental shop names the user would like to search for."
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