from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CancelKayakReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    booking_id: str = Field(..., description="The unique identifier for the existing kayak reservation.")
    reason: str = Field(..., description="The reason provided by the user for cancelling.")

    model_config = ConfigDict(extra="forbid")

class CancelKayakReservationOutputModel(BaseModel):
    status: str = Field(..., description="The status of the cancellation attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the cancellation outcome.")
    refund_status: Optional[str] = Field(default=None, description="Indicates the refund outcome (e.g., 'Full Refund' or 'No Refund').")
    refund_amount: Optional[float] = Field(default=None, description="The amount refunded to the user.")

    model_config = ConfigDict(extra="forbid")