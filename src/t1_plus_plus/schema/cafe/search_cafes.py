from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchCafesInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a cafe at.",
    )
    cafe_type: Optional[str] = Field(
        default=None,
        description="Type of cafe: 'Coffee Shop' or 'Bubble Tea'. If not provided, searches both.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would like to look for a cafe at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating the user is willing to consider.",
    )
    cafe_name: Optional[List[str]] = Field(
        default=None,
        description="List of cafe names the user would like to look at.",
    )
    cafe_id: Optional[List[str]] = Field(
        default=None,
        description="List of cafe IDs the user would like to look at.",
    )
    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user per person.",
    )
    price_level: Optional[List[str]] = Field(
        default=None,
        description="List of price levels the user is willing to consider, e.g., ['$', '$$'].",
    )

    # --- Coffee Shop: Roast Types ---
    has_light_roast: Optional[bool] = Field(default=None, description="True or False.")
    has_medium_roast: Optional[bool] = Field(default=None, description="True or False.")
    has_dark_roast: Optional[bool] = Field(default=None, description="True or False.")
    has_single_origin: Optional[bool] = Field(
        default=None, description="True or False."
    )
    has_house_blend: Optional[bool] = Field(default=None, description="True or False.")

    # --- Shared: Milk Alternatives ---
    has_oat: Optional[bool] = Field(default=None, description="True or False.")
    has_almond: Optional[bool] = Field(default=None, description="True or False.")
    has_soy: Optional[bool] = Field(default=None, description="True or False.")
    has_coconut: Optional[bool] = Field(default=None, description="True or False.")
    has_macadamia: Optional[bool] = Field(default=None, description="True or False.")
    has_pistachio: Optional[bool] = Field(default=None, description="True or False.")

    # --- Coffee Shop: Sugar Levels ---
    has_no_sugar: Optional[bool] = Field(default=None, description="True or False.")
    has_light: Optional[bool] = Field(default=None, description="True or False.")
    has_regular: Optional[bool] = Field(default=None, description="True or False.")
    has_extra: Optional[bool] = Field(default=None, description="True or False.")

    # --- Coffee Shop: Flavor Additions ---
    has_vanilla: Optional[bool] = Field(default=None, description="True or False.")
    has_caramel: Optional[bool] = Field(default=None, description="True or False.")
    has_hazelnut: Optional[bool] = Field(default=None, description="True or False.")
    has_mocha: Optional[bool] = Field(default=None, description="True or False.")
    has_pumpkin_spice: Optional[bool] = Field(
        default=None, description="True or False."
    )

    # --- Bubble Tea: Sugar Levels ---
    has_0pct: Optional[bool] = Field(default=None, description="True or False.")
    has_25pct: Optional[bool] = Field(default=None, description="True or False.")
    has_50pct: Optional[bool] = Field(default=None, description="True or False.")
    has_75pct: Optional[bool] = Field(default=None, description="True or False.")
    has_100pct: Optional[bool] = Field(default=None, description="True or False.")
    has_120pct: Optional[bool] = Field(default=None, description="True or False.")

    # --- Bubble Tea: Ice Levels ---
    has_no_ice: Optional[bool] = Field(default=None, description="True or False.")
    has_less_ice: Optional[bool] = Field(default=None, description="True or False.")
    has_regular_ice: Optional[bool] = Field(default=None, description="True or False.")
    has_extra_ice: Optional[bool] = Field(default=None, description="True or False.")

    # --- Bubble Tea: Tea Bases ---
    has_black_tea: Optional[bool] = Field(default=None, description="True or False.")
    has_jasmine_green: Optional[bool] = Field(
        default=None, description="True or False."
    )
    has_oolong: Optional[bool] = Field(default=None, description="True or False.")
    has_matcha: Optional[bool] = Field(default=None, description="True or False.")
    has_taro: Optional[bool] = Field(default=None, description="True or False.")
    has_thai_tea: Optional[bool] = Field(default=None, description="True or False.")
    has_fruit_tea: Optional[bool] = Field(default=None, description="True or False.")

    # --- Bubble Tea: Toppings ---
    has_brown_sugar_pearls: Optional[bool] = Field(
        default=None, description="True or False."
    )
    has_crystal_boba: Optional[bool] = Field(default=None, description="True or False.")
    has_popping_boba: Optional[bool] = Field(default=None, description="True or False.")
    has_lychee_jelly: Optional[bool] = Field(default=None, description="True or False.")
    has_grass_jelly: Optional[bool] = Field(default=None, description="True or False.")
    has_cheese_foam: Optional[bool] = Field(default=None, description="True or False.")
    has_egg_pudding: Optional[bool] = Field(default=None, description="True or False.")
    has_aloe_vera: Optional[bool] = Field(default=None, description="True or False.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("cafe_type", mode="before")
    @classmethod
    def validate_cafe_type(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        valid = ["Coffee Shop", "Bubble Tea"]
        if value not in valid:
            raise ValueError(f"cafe_type must be one of {valid}. Got '{value}'.")
        return value

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
