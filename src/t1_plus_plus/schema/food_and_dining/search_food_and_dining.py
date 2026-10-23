from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchFoodAndDiningInputModel(BaseModel):
    city: str = Field(..., description="City to search in. Required.")
    state: str = Field(..., description="State abbreviation (e.g., 'TX', 'CA'). Required when city is provided.")
    neighborhood: Optional[List[str]] = Field(default=None, description="List of neighborhoods to filter by.")
    rating: Optional[List[float]] = Field(
        default=None, description="[min_rating, max_rating] range (e.g., [4.0, 5.0])."
    )
    restaurant_name: Optional[List[str]] = Field(default=None, description="List of establishment names.")
    restaurant_id: Optional[List[str]] = Field(default=None, description="List of establishment IDs.")
    price_per_person: Optional[float] = Field(default=None, description="Maximum price per person budget.")
    price_level: Optional[List[str]] = Field(
        default=None, description="Price level(s) to filter by (e.g., ['$', '$$', '$$$', '$$$$'])."
    )

    # --- Cuisine ---
    cuisine: Optional[List[str]] = Field(default=None, description="List of cuisine types (e.g., ['Italian', 'Thai']).")

    # --- Service features ---
    is_open: Optional[bool] = Field(default=None, description="True or False.")
    is_open_24_7: Optional[bool] = Field(default=None, description="True or False.")
    has_drive_thru: Optional[bool] = Field(default=None, description="True or False.")
    has_curbside_pickup: Optional[bool] = Field(default=None, description="True or False.")
    has_mobile_ordering_app: Optional[bool] = Field(default=None, description="True or False.")
    has_self_service_kiosks: Optional[bool] = Field(default=None, description="True or False.")
    has_free_wifi: Optional[bool] = Field(default=None, description="True or False.")
    has_play_area: Optional[bool] = Field(default=None, description="True or False.")

    # --- Delivery ---
    supports_delivery: Optional[bool] = Field(default=None, description="True if the establishment offers delivery.")
    supports_third_party_delivery: Optional[bool] = Field(
        default=None, description="True if the establishment supports third-party delivery apps."
    )

    # --- Dietary options ---
    vegan_options: Optional[bool] = Field(default=None, description="True or False.")
    vegetarian_options: Optional[bool] = Field(default=None, description="True or False.")
    gluten_free_options: Optional[bool] = Field(default=None, description="True or False.")
    halal_options: Optional[bool] = Field(default=None, description="True or False.")
    kosher_options: Optional[bool] = Field(default=None, description="True or False.")
    low_carb_options: Optional[bool] = Field(default=None, description="True or False.")
    nut_allergy_options: Optional[bool] = Field(default=None, description="True or False.")
    dairy_allergy_options: Optional[bool] = Field(default=None, description="True or False.")
    shell_fish_allergy_options: Optional[bool] = Field(default=None, description="True or False.")
    tomato_allergy_options: Optional[bool] = Field(default=None, description="True or False.")
    nightshade_allergy_options: Optional[bool] = Field(default=None, description="True or False.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("rating", mode="before")
    @classmethod
    def validate_rating(cls, value: Any) -> List[float]:
        if not isinstance(value, list):
            raise ValueError("rating must be a list [min, max].")
        if len(value) != 2:
            raise ValueError("rating must contain exactly two elements.")
        return [float(v) for v in value]


