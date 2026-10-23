from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SearchCruisesInputModel(BaseModel):
    destination: Optional[str] = Field(default=None, description="The destination region of the cruise (e.g., 'Caribbean - Eastern', 'Alaska').")
    departure_port: Optional[str] = Field(default=None, description="The port the cruise departs from (e.g., 'Miami', 'Seattle').")
    cruise_line: Optional[List[str]] = Field(default=None, description="List of preferred cruise lines (e.g., 'Carnival Cruise Line').")
    duration_nights: Optional[List[int]] = Field(default=None, description="List of preferred cruise durations in nights.")
    tier: Optional[int] = Field(default=None, description="Cruise tier: 1 (Contemporary), 2 (Premium), 3 (Luxury).")
    rating: Optional[List[float]] = Field(default=None, description="Consists of the [min, max] rating the user is willing to consider.")
    cabin_type: Optional[str] = Field(default=None, description="Preferred cabin type (e.g., 'interior', 'ocean_view', 'balcony', 'suite', 'penthouse_suite').")
    price_per_person_max: Optional[int] = Field(default=None, description="Max budget per person for the preferred cabin type.")

    # Select Boolean Features
    has_wifi: Optional[bool] = Field(default=None)
    wifi_included: Optional[bool] = Field(default=None)
    gratuities_included: Optional[bool] = Field(default=None)
    beverages_included: Optional[bool] = Field(default=None)
    is_adults_only: Optional[bool] = Field(default=None)
    has_swimming_pools: Optional[bool] = Field(default=None)
    has_casino: Optional[bool] = Field(default=None)
    has_kids_club: Optional[bool] = Field(default=None)
    has_butler_service: Optional[bool] = Field(default=None)

    model_config = ConfigDict(extra="forbid")

    @field_validator("rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> Optional[List[float]]:
        if value is None: return value
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("Rating must be a list of [min, max].")
        return [float(v) for v in value]
