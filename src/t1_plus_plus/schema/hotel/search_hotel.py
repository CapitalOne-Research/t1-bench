from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchHotelInputModel(BaseModel):
    city: str = Field(
        ...,
        description="City the user would like to look for a hotel in.",
    )
    state: Optional[str] = Field(
        default=None,
        description="State the user would like to look for a hotel in.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would like to look for a hotel in.",
    )
    star_rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum star rating the user is willing to consider for a hotel.",
    )
    hotel_name: Optional[List[str]] = Field(
        default=None,
        description="List of hotel names the user would like to look at.",
    )
    hotel_id: Optional[List[str]] = Field(
        default=None,
        description="List of hotel IDs the user would like to look at.",
    )
    brand: Optional[List[str]] = Field(
        default=None,
        description="List of hotel brands the user would like to look at (e.g., Aura, Apex, Verve, Nomad).",
    )
    has_pool: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with a pool. True or False.",
    )
    has_gym: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with a gym. True or False.",
    )
    has_spa: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with a spa. True or False.",
    )
    has_digital_key: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with digital key access. True or False.",
    )
    has_valet_parking: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with valet parking. True or False.",
    )
    has_business_center: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with a business center. True or False.",
    )
    is_pet_friendly: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a pet friendly hotel. True or False.",
    )
    has_electric_vehicle_charging: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with EV charging. True or False.",
    )
    has_childcare_services: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with childcare services. True or False.",
    )
    has_shuttle_service: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with a shuttle service. True or False.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("star_rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> List[float]:
        if not type(value) is list:
            raise ValueError(f"star_rating must be a list. got {type(value)}")
        if len(value) != 2:
            raise ValueError("star_rating must contain exactly two items representing a min and max.")
        result = []
        for v in value:
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                raise ValueError(
                    "Each item in the list must be either an integer or a float."
                )
        return result