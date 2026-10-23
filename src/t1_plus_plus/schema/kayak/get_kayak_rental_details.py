from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from t1_plus_plus.schema.kayak.kayak_rental_item import KayakRentalItem






class GetRentalDetailsInputModel(BaseModel):
    rental_id: str = Field(..., description="The unique identifier for the specific rental business (e.g., 'KYK-20000').")

    model_config = ConfigDict(extra="forbid")


class GetRentalDetailsOutputModel(BaseModel):
    status: str = Field(..., description="The status of the retrieval attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the retrieval outcome.")
    rental_details: Optional[KayakRentalItem] = Field(
        default=None, 
        description="The complete details for the requested rental ID."
    )

    model_config = ConfigDict(extra="forbid")