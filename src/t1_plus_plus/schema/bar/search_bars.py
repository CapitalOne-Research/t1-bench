from datetime import datetime, time
from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchBarsInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a bar at.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would look to look for a bar at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum rating the user is willing to consider for a bar.",
    )
    bar_name: Optional[List[str]] = Field(
        default=None,
        description="List of bar names the user would like to look at",
    )
    bar_id: Optional[List[str]] = Field(
        default=None,
        description="List of bar IDs the user would like to look at",
    )
    bar_type: Optional[List[str]] = Field(
        default=None,
        description="List of bar types the user would like to look at (e.g., Speakeasy, Dive Bar, Sports Bar).",
    )
    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user for a bar per person",
    )
    has_happy_hour: Optional[bool] = Field(
        default=None,
        description="Whether or not user wants a bar with happy hour options True or False.",
    )
    has_live_music: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with live music options. True or False.",
    )
    has_dj: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with a DJ. True or False.",
    )
    has_pool_tables: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with pool tables. True or False.",
    )
    has_dance_floor: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with a dance floor. True or False.",
    )
    has_smoking_area: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with smoking area. True or False.",
    )
    has_karaoke: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with karaoke options. True or False.",
    )
    has_sports_games: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with sports games True or False.",
    )
    has_tvs: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with TVs. True or False.",
    )
    has_trivia: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with trivia. True or False.",
    )
    has_late_night_food_menu: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with late night food menu. True or False.",
    )
    has_darts: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with darts. True or False.",
    )
    has_foosball: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with foosball. True or False.",
    )
    has_waterfront_view: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with waterfront view. True or False.",
    )
    has_coat_check: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with coat check. True or False.",
    )
    has_valet_parking: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with valet parking. True or False.",
    )
    has_phone_charging_stations: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with darts. True or False.",
    )
    has_wheelchair_accessible: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with foosball. True or False.",
    )
    has_free_wifi: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with free wifi. True or False.",
    )
    has_vegan_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with vegan options. True or False.",
    )
    has_vegetarian_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with vegetarian options. True or False.",
    )
    has_gluten_free_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with gluten free options. True or False.",
    )
    has_halal_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with halal options. True or False.",
    )
    has_kosher_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with kosher options. True or False.",
    )
    has_low_carb_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with low carb options. True or False.",
    )
    has_nut_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with nut allergy options. True or False.",
    )
    has_dairy_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with dairy allergy options. True or False.",
    )
    has_shell_fish_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with shell fish allergy options. True or False.",
    )
    has_tomato_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with tomato allergy options. True or False.",
    )
    has_nightshade_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with nightshade allergy options. True or False.",
    )
    has_craft_beer: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with craft beer. True or False.",
    )
    has_natural_wine: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with natural wine. True or False.",
    )
    has_classic_cocktails: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with classic cocktails. True or False.",
    )
    has_signature_mixology: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with signature mixology. True or False.",
    )
    has_sake: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with sake. True or False.",
    )
    has_whiskey_flight: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with whiskey flight. True or False.",
    )
    has_mocktails: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with mocktails. True or False.",
    )
    has_vip_lounge: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with a VIP lounge. True or False.",
    )
    has_vip_room_upgrade: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with a VIP room upgrade. True or False.",
    )
    cover_fee_max: Optional[int] = Field(
        default=None,
        description="Maximum cover fee the user is willing to pay for a bar.",
    )
    event_occupancy: Optional[int] = Field(
        default=None,
        description="Maximum event occupancy the user is willing to consider for a bar.",
    )
    minimum_age: Optional[int] = Field(
        default=None,
        description="Minimum age the user is willing to consider for a bar.",
    )
    has_intimate_vibes: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with intimate vibes. True or False.",
    )
    has_social_vibes: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with social vibes. True or False.",
    )
    has_fun_vibes: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a bar with fun vibes. True or False.",
    )
    time_range: Optional[List[str]] = Field(
        default=None,
        description="Time range the user is willing to consider for a bar. Format: ['HH:MM', 'HH:MM'].",
    )

    model_config = ConfigDict(extra="forbid")

    # FIX 1: Add ClassVar type annotation here
    time_formats: ClassVar[List[str]] = [
        "%H:%M",  # 14:30
        "%I:%M %p",  # 02:30 PM
        "%I:%M%p",  # 02:30PM
        "%I %p",  # 02 PM
        "%I%p",  # 02PM
    ]

    @field_validator("time_range", mode="before")
    @classmethod
    def normalize_time_range(cls, values: Any) -> Optional[List[str]]:
        if values is None:
            return values

        if not isinstance(values, list):
            raise ValueError(
                "time_range must be a list containing a start and end time."
            )

        if len(values) != 2:
            raise ValueError(
                f"time_range must contain exactly two elements: [start_time, end_time]. Got {len(values)}."
            )

        def normalize(t: Any) -> str:
            # FIX 2: Ensure 'time' and 'datetime' are imported at the top of the file
            if isinstance(t, time):
                return t.strftime("%H:%M")

            if not isinstance(t, str):
                raise ValueError(
                    f"Invalid time passed. Expected string or time object, got: {type(t)}"
                )

            t_str = t.strip()
            for fmt in cls.time_formats:
                try:
                    return datetime.strptime(t_str, fmt).strftime("%H:%M")
                except ValueError:
                    continue
            raise ValueError(f"Unrecognized time format: '{t_str}'")

        return [normalize(values[0]), normalize(values[1])]

    @field_validator(
        "budget",
        mode="before",
    )
    @classmethod
    def enforce_int_type(cls, value: Any) -> int:
        if type(value) is int:
            return value
        if type(value) is str and value.isdigit():
            return int(value)
        raise ValueError("Value must be an integer or numeric string.")

    @field_validator("rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> List[float]:
        if not type(value) is list:
            raise ValueError(f"ratings must be a list. got {type(value)}")
        if len(value) != 2:
            raise ValueError("ratings must contain exactly two items.")
        result = []
        for v in value:
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                raise ValueError(
                    "Each item in the list must be either an integer or a float."
                )
        return result
