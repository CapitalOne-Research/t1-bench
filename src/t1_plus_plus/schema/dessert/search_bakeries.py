from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchBakeriesInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a bakery at.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would like to look for a bakery at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating the user is willing to consider.",
    )
    bakery_name: Optional[List[str]] = Field(
        default=None,
        description="List of bakery names the user would like to look at.",
    )
    bakery_id: Optional[List[str]] = Field(
        default=None,
        description="List of bakery IDs the user would like to look at.",
    )
    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user per person.",
    )
    price_level: Optional[List[str]] = Field(
        default=None,
        description="List of price levels the user is willing to consider, e.g., ['$', '$$', '$$$', '$$$$'].",
    )

    # --- Bread Specialties ---
    has_sourdough: Optional[bool] = Field(default=None, description="True or False.")
    has_viennoiserie: Optional[bool] = Field(default=None, description="True or False.")
    has_artisan_bread: Optional[bool] = Field(default=None, description="True or False.")
    has_custom_cakes: Optional[bool] = Field(default=None, description="True or False.")
    has_pastries: Optional[bool] = Field(default=None, description="True or False.")

    # --- Service Options ---
    has_retail: Optional[bool] = Field(default=None, description="True or False.")
    has_wholesale: Optional[bool] = Field(default=None, description="True or False.")
    has_custom_orders: Optional[bool] = Field(default=None, description="True or False.")
    has_wedding_cakes: Optional[bool] = Field(default=None, description="True or False.")

    # --- Dietary Options (matching CSV column names) ---
    has_has_vegan_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_vegetarian_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_gluten_free_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_sugar_free_baked_goods: Optional[bool] = Field(default=None, description="True or False.")
    has_yeast_free_options: Optional[bool] = Field(default=None, description="True or False.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("budget", mode="before")
    @classmethod
    def enforce_int_type(cls, value: Any) -> Optional[int]:
        if value is None:
            return value
        if type(value) is int:
            return value
        if type(value) is str and value.isdigit():
            return int(value)
        raise ValueError("Value must be an integer or numeric string.")

    @field_validator("rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> Optional[List[float]]:
        if value is None:
            return value
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("Rating must be a list of [min, max].")
        return [float(v) for v in value]
