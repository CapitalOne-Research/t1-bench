from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchDessertShopsInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a dessert shop at.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would like to look for a dessert shop at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating the user is willing to consider.",
    )
    shop_name: Optional[List[str]] = Field(
        default=None,
        description="List of dessert shop names the user would like to look at.",
    )
    shop_id: Optional[List[str]] = Field(
        default=None,
        description="List of dessert shop IDs the user would like to look at.",
    )
    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user per person.",
    )
    price_level: Optional[List[str]] = Field(
        default=None,
        description="List of price levels the user is willing to consider, e.g., ['$', '$$'].",
    )

    # --- Dessert Categories ---
    has_ice_cream: Optional[bool] = Field(default=None, description="True or False.")
    has_gelato: Optional[bool] = Field(default=None, description="True or False.")
    has_frozen_yogurt: Optional[bool] = Field(default=None, description="True or False.")
    has_chocolatier: Optional[bool] = Field(default=None, description="True or False.")
    has_cheesecake: Optional[bool] = Field(default=None, description="True or False.")
    has_red_velvet: Optional[bool] = Field(default=None, description="True or False.")
    has_cupcakes: Optional[bool] = Field(default=None, description="True or False.")
    has_brownies: Optional[bool] = Field(default=None, description="True or False.")
    has_cookies: Optional[bool] = Field(default=None, description="True or False.")
    has_tarts: Optional[bool] = Field(default=None, description="True or False.")
    has_creperie: Optional[bool] = Field(default=None, description="True or False.")
    has_donuts: Optional[bool] = Field(default=None, description="True or False.")
    has_patisserie: Optional[bool] = Field(default=None, description="True or False.")
    has_candy_store: Optional[bool] = Field(default=None, description="True or False.")
    has_pie_shop: Optional[bool] = Field(default=None, description="True or False.")
    has_pudding_custard: Optional[bool] = Field(default=None, description="True or False.")
    has_milkshake: Optional[bool] = Field(default=None, description="True or False.")
    has_frappe: Optional[bool] = Field(default=None, description="True or False.")
    has_soda_float: Optional[bool] = Field(default=None, description="True or False.")
    has_pudding: Optional[bool] = Field(default=None, description="True or False.")

    # --- Temperature Profiles ---
    has_frozen: Optional[bool] = Field(default=None, description="True or False.")
    has_chilled: Optional[bool] = Field(default=None, description="True or False.")
    has_warm: Optional[bool] = Field(default=None, description="True or False.")
    has_room_temperature: Optional[bool] = Field(default=None, description="True or False.")

    # --- Toppings ---
    has_fresh_fruit: Optional[bool] = Field(default=None, description="True or False.")
    has_hot_fudge: Optional[bool] = Field(default=None, description="True or False.")
    has_caramel: Optional[bool] = Field(default=None, description="True or False.")
    has_whipped_cream: Optional[bool] = Field(default=None, description="True or False.")
    has_sprinkles: Optional[bool] = Field(default=None, description="True or False.")
    has_crushed_cookies: Optional[bool] = Field(default=None, description="True or False.")
    has_nuts: Optional[bool] = Field(default=None, description="True or False.")
    has_gummy_candies: Optional[bool] = Field(default=None, description="True or False.")
    has_mochi_bits: Optional[bool] = Field(default=None, description="True or False.")
    has_peanut_butter: Optional[bool] = Field(default=None, description="True or False.")

    # --- Dietary Options (matching CSV column names) ---
    has_has_dairy_free_scoops: Optional[bool] = Field(default=None, description="True or False.")
    has_has_sugar_free_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_egg_free_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_gelatin_free_options: Optional[bool] = Field(default=None, description="True or False.")
    has_has_nut_free_facility: Optional[bool] = Field(default=None, description="True or False.")
    has_is_vegan_friendly: Optional[bool] = Field(default=None, description="True or False.")

    # --- Features ---
    has_sample_spoons_available: Optional[bool] = Field(default=None, description="True or False.")
    has_custom_toppings_bar: Optional[bool] = Field(default=None, description="True or False.")
    has_custom_cake_ordering: Optional[bool] = Field(default=None, description="True or False.")
    has_gift_boxes: Optional[bool] = Field(default=None, description="True or False.")
    has_seasonal_flavors: Optional[bool] = Field(default=None, description="True or False.")

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
