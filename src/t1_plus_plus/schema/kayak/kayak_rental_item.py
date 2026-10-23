# File: t1_plus_plus/tools/schema/kayak_rental_item.py

from pydantic import BaseModel, Field

class KayakRentalItem(BaseModel):
    """Represents a single rental listing from the dataset."""
    
    rental_id: str = Field(..., description="Unique identifier for the rental business.")
    business_name: str = Field(..., description="The name of the rental shop.")
    city: str = Field(..., description="The city where the rental is located.")
    state: str = Field(..., description="The two-letter state code.")
    neighborhood: str = Field(..., description="The specific local area within the city.")
    latitude: float = Field(..., description="The geographic latitude coordinate.")
    longitude: float = Field(..., description="The geographic longitude coordinate.")
    vessel_type: str = Field(
        ..., 
        description="The specific craft available for rent. Examples: 'Single (Sit-on-Top)', 'Tandem', 'SUP'."
    )
    price_per_hour: float = Field(..., description="The cost in USD for a one-hour rental.")
    rating: float = Field(..., description="The user satisfaction score (1.0 to 5.0).")