from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Attraction(BaseModel):
    city: str = Field(..., description="City where the attraction is located.")
    state: str = Field(..., description="Two-letter state code for the attraction.")
    name: str = Field(..., description="Name of the attraction.")
    type: str = Field(..., description="Category of the attraction, such as Art, Sports, or Scenery.")
    latitude: float = Field(..., description="Latitude of the attraction.")
    longitude: float = Field(..., description="Longitude of the attraction.")
    rating: float = Field(..., ge=0.0, le=5.0, description="Rating for the attraction.")
    distance_miles: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional computed distance from a reference point in miles.",
    )

    model_config = ConfigDict(extra="forbid")


class SearchAttractionsInputModel(BaseModel):
    city: str | None = Field(
        default=None,
        description="City to search for attractions in.",
    )
    state: str | None = Field(
        default=None,
        description="State to search for attractions in.",
    )
    attraction_type: str | None = Field(
        default=None,
        description="Attraction type to filter by.",
    )
    min_rating: float | None = Field(
        default=None,
        description="Minimum rating the user is willing to consider.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("city", "state", "attraction_type", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Value must be a string.")
        value = value.strip()
        return value or None

    @field_validator("min_rating", mode="before")
    @classmethod
    def normalize_min_rating(cls, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("min_rating must be a number.")
        if not 0 <= value <= 5:
            raise ValueError("min_rating must be between 0 and 5.")
        return value


class FilterAttractionsInputModel(BaseModel):
    cache_key: str = Field(
        ...,
        description="The cache key used to retrieve prior attraction search results (e.g., 'search_attractions_results_0').",
    )
    city: str | None = Field(
        default=None,
        description="City to filter attractions by.",
    )
    state: str | None = Field(
        default=None,
        description="State to filter attractions by.",
    )
    attraction_type: str | None = Field(
        default=None,
        description="Attraction type to filter by.",
    )
    min_rating: float | None = Field(
        default=None,
        description="Minimum rating to include.",
    )
    max_rating: float | None = Field(
        default=None,
        description="Maximum rating to include.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("city", "state", "attraction_type", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Value must be a string.")
        value = value.strip()
        return value or None

    @field_validator("min_rating", "max_rating", mode="before")
    @classmethod
    def normalize_rating(cls, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Rating must be a number.")
        if not 0 <= value <= 5:
            raise ValueError("Rating must be between 0 and 5.")
        return value


class GetAttractionDetailsInputModel(BaseModel):
    name: str = Field(..., description="Name of the attraction to retrieve.")
    city: str | None = Field(default=None, description="Optional city filter.")
    state: str | None = Field(default=None, description="Optional state filter.")

    model_config = ConfigDict(extra="forbid")


class GetTopAttractionsInputModel(BaseModel):
    city: str = Field(..., description="City to retrieve top attractions for.")
    state: str | None = Field(default=None, description="Optional state filter.")
    attraction_type: str | None = Field(default=None, description="Optional attraction type filter.")

    model_config = ConfigDict(extra="forbid")


class GetNearbyAttractionsInputModel(BaseModel):
    latitude: float | None = Field(default=None, description="Reference latitude. Required if attraction_name is not provided.")
    longitude: float | None = Field(default=None, description="Reference longitude. Required if attraction_name is not provided.")
    attraction_name: str | None = Field(default=None, description="Name of a known attraction to use as the search origin. If provided, its coordinates are looked up automatically.")
    attraction_city: str | None = Field(default=None, description="City of the named attraction, used to disambiguate when attraction_name is provided.")
    radius_miles: float = Field(default=10.0, gt=0.0, le=250.0, description="Search radius in miles.")
    attraction_type: str | None = Field(default=None, description="Optional attraction type filter.")
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0, description="Minimum attraction rating.")

    model_config = ConfigDict(extra="forbid")


class GetAttractionDetailsOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the retrieval attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message regarding the retrieval outcome.",
    )
    attraction: Optional[Attraction] = Field(
        default=None,
        description="The matching attraction details.",
    )

    model_config = ConfigDict(extra="forbid")


class GetTopAttractionsOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the retrieval attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message regarding the retrieval outcome.",
    )
    attractions: List[Attraction] = Field(
        default_factory=list,
        description="List of top-rated attractions.",
    )

    model_config = ConfigDict(extra="forbid")


class GetNearbyAttractionsOutputModel(BaseModel):
    status: str = Field(
        ...,
        description="The status of the retrieval attempt (e.g., 'success' or 'error').",
    )
    message: str = Field(
        ...,
        description="A descriptive message regarding the retrieval outcome.",
    )
    attractions: List[Attraction] = Field(
        default_factory=list,
        description="List of nearby attractions.",
    )

    model_config = ConfigDict(extra="forbid")


