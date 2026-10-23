from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime


class FilterFlightsInputModel(BaseModel):
    cache_key: str = Field(
        ...,
        description="The cache key used to retrieve prior flight search results (e.g., 'previous_flights').",
    )
    airline: Optional[List[str]] = Field(
        default=None,
        description="List of preferred airlines (e.g., ['AeroOne', 'Blue Horizon Airlines', 'SkyReach Airways']).",
    )
    price_max: Optional[float] = Field(
        default=None,
        description="Maximum price per ticket.",
    )
    departure_time_after: Optional[str] = Field(
        default=None,
        description="Earliest acceptable departure time in HH:MM format (e.g., '08:00').",
    )
    departure_time_before: Optional[str] = Field(
        default=None,
        description="Latest acceptable departure time in HH:MM format (e.g., '18:00').",
    )
    ticket_class: Optional[str] = Field(
        default=None,
        description="The ticket class (e.g., 'Economy', 'Business', 'First').",
    )
    departure_date: Optional[str] = Field(
        default=None,
        description="The departure date in YYYY-MM-DD format.",
    )
    arrival_date: Optional[str] = Field(
        default=None,
        description="The arrival date in YYYY-MM-DD format.",
    )
    departure_airport: Optional[str] = Field(
        default=None,
        description="The departure airport code (e.g., 'LAX', 'JFK', 'SFO').",
    )
    arrival_airport: Optional[str] = Field(
        default=None,
        description="The arrival airport code (e.g., 'SFO', 'MIA', 'ATL').",
    )
    departure_city: Optional[str] = Field(
        default=None,
        description="The departure city name (e.g., 'Los Angeles', 'New York', 'San Francisco').",
    )
    arrival_city: Optional[str] = Field(
        default=None,
        description="The arrival city name (e.g., 'San Francisco', 'Miami', 'Atlanta').",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("departure_date", "arrival_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Date must be in 'YYYY-MM-DD' format.")

    @field_validator("departure_time_after", "departure_time_before", mode="before")
    @classmethod
    def validate_time(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            raise ValueError("Time must be in 'HH:MM' format (e.g., '08:00').")
