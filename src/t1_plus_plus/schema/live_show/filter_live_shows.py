from datetime import date, datetime, time
from typing import Any, ClassVar, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from t1_plus_plus.schema.general.search_output import SearchResultsOutputModel


class FilterLiveShowsInputModel(BaseModel):
    cache_key: str = Field(
        ...,
        description="The cache key used to retrieve prior live show search results.",
    )
    live_event_id: Optional[List[str]] = Field(
        default=None,
        description="List of specific live event IDs to filter by (e.g., ['LE0', 'LE5']).",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods to filter venues by.",
    )
    venue_type: Optional[List[str]] = Field(
        default=None,
        description="Type of venue (e.g., 'Concert Hall', 'Theater', 'Club').",
    )
    event_category: Optional[List[str]] = Field(
        default=None,
        description="List of event categories. Valid values: 'Concert', 'Play', 'Musical', 'Opera', 'Ballet', 'Standup comedy', 'Jazz', 'Circus show'.",
    )
    show_name: Optional[str] = Field(
        default=None,
        description="Specific name of the show to search for.",
    )
    performer: Optional[str] = Field(
        default=None,
        description="Name of the performer or band.",
    )
    is_outdoors: Optional[bool] = Field(
        default=None,
        description="Whether the venue is outdoors.",
    )
    parking_available: Optional[bool] = Field(
        default=None,
        description="Whether parking is available at the venue.",
    )
    serves_food: Optional[bool] = Field(
        default=None,
        description="Whether the venue serves food.",
    )
    serves_alcohol: Optional[bool] = Field(
        default=None,
        description="Whether the venue serves alcohol.",
    )
    family_friendly: Optional[bool] = Field(
        default=None,
        description="Filter for shows that are family friendly.",
    )
    seat_location: Optional[List[Literal["front", "middle", "back"]]] = Field(
        default=None,
        description="List of preferred seat locations. Will only return shows where at least one of these sections has availability.",
    )
    price_range: Optional[List[float]] = Field(
        default=None,
        description="Minimum and maximum price (USD) the user is willing to pay. Format: [min, max].",
    )
    event_date_range: Optional[List[str]] = Field(
        default=None,
        description="Date range for the show. Format: ['YYYY-MM-DD', 'YYYY-MM-DD'].",
    )
    time_range: Optional[List[str]] = Field(
        default=None,
        description="Time range the show starts within. Format: ['HH:MM', 'HH:MM'].",
    )

    model_config = ConfigDict(extra="forbid")

    time_formats: ClassVar[List[str]] = [
        "%H:%M",
        "%I:%M %p",
        "%I:%M%p",
        "%I %p",
        "%I%p",
    ]

    @field_validator("time_range", mode="before")
    @classmethod
    def normalize_time_range(cls, values: Any) -> Optional[List[str]]:
        if values is None:
            return values
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError("time_range must contain exactly two elements: [start_time, end_time].")
        def normalize(t: Any) -> str:
            if isinstance(t, time): return t.strftime("%H:%M")
            if not isinstance(t, str): raise ValueError(f"Invalid time format: {type(t)}")
            t_str = t.strip()
            for fmt in cls.time_formats:
                try: return datetime.strptime(t_str, fmt).strftime("%H:%M")
                except ValueError: continue
            raise ValueError(f"Unrecognized time format: '{t_str}'")
        return [normalize(values[0]), normalize(values[1])]

    @field_validator("event_date_range", mode="before")
    @classmethod
    def normalize_date_range(cls, values: Any) -> Optional[List[str]]:
        if values is None: return values
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError("event_date_range must contain exactly two elements: [start_date, end_date].")
        def normalize_date(d: Any) -> str:
            if isinstance(d, (date, datetime)): return d.strftime("%Y-%m-%d")
            if not isinstance(d, str): raise ValueError(f"Invalid date format: {type(d)}")
            try: return datetime.strptime(d.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError: raise ValueError(f"Date must be in YYYY-MM-DD format, got: '{d}'")
        return [normalize_date(values[0]), normalize_date(values[1])]

    @field_validator("price_range", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> Optional[List[float]]:
        if value is None: return None
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("price_range must contain exactly two numbers [min, max].")
        try: return [float(v) for v in value]
        except (ValueError, TypeError): raise ValueError("Items in price_range must be numeric.")