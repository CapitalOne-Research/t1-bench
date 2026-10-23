from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# -----------------------------------------------------------------------
# Menu Models
# -----------------------------------------------------------------------
class CafeMenuItem(BaseModel):
    item_id: str = Field(..., description="Unique ID for the menu item, required for ordering.")
    item_name: str = Field(..., description="Name of the menu item.")
    description: str = Field(..., description="Description of the item.")
    base_price: float = Field(..., description="Base price of the item.")
    dietary_tags: List[str] = Field(default_factory=list, description="List of dietary tags.")
    allergens: List[str] = Field(default_factory=list, description="List of allergens present.")


class GetCafeMenuInputModel(BaseModel):
    cafe_id: str = Field(..., description="The unique identifier for the cafe location.")

    model_config = ConfigDict(extra="forbid")


class GetCafeMenuOutputModel(BaseModel):
    status: str = Field(..., description="The status of the retrieval attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the retrieval outcome.")
    cafe_name: Optional[str] = Field(default=None, description="The name of the cafe.")
    cafe_type: Optional[str] = Field(default=None, description="The type of cafe: 'Coffee Shop' or 'Bubble Tea'.")
    menu_items: List[CafeMenuItem] = Field(default_factory=list, description="List of available menu items.")

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------
# Order Item Models
# -----------------------------------------------------------------------
class OrderItemInput(BaseModel):
    """What the agent passes for each item in an order."""
    item_id: str = Field(..., description="The unique identifier for the menu item.")
    quantity: int = Field(..., description="The number of this specific item ordered. Must be at least 1.")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Quantity must be at least 1.")
        return value


class OrderItem(BaseModel):
    """Represents a single line item in a placed cafe order."""
    item_id: str = Field(..., description="The unique identifier for the menu item.")
    quantity: int = Field(..., description="The number of this specific item ordered.")
    line_total: float = Field(..., description="The total cost for this line item (unit price * quantity).")


class CafeOrder(BaseModel):
    """Represents a placed cafe order."""
    order_id: str = Field(..., description="Unique ID for the cafe order.")
    user_id: str = Field(..., description="ID of the user who placed the order.")
    cafe_id: str = Field(..., description="ID of the cafe location.")
    items: List[OrderItem] = Field(..., description="List of ordered items with quantities and line totals.")
    payment_method: str = Field(..., description="Payment method used (e.g., 'credit_card', 'debit_card', 'gift_card').")
    promo_code: Optional[str] = Field(default=None, description="Promo code applied to the order, if any.")
    subtotal: float = Field(..., description="Subtotal before tax and discounts.")
    tax: float = Field(..., description="Tax amount applied.")
    total: float = Field(..., description="The final total amount charged.")
    status: str = Field(
        ...,
        description="Current status: 'Placed', 'Preparing', 'Ready_for_Pickup', 'Completed', 'Cancelled'.",
    )


# -----------------------------------------------------------------------
# Place Order
# -----------------------------------------------------------------------
class PlaceCafeOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    cafe_id: str = Field(..., description="The unique identifier for the cafe location.")
    items: List[OrderItemInput] = Field(..., description="List of items to order, including item_id and quantity.")
    payment_method: str = Field(
        ..., description="Payment method: 'credit_card', 'debit_card', or 'gift_card'."
    )
    promo_code: Optional[str] = Field(default=None, description="Promo code applied to the order, if any.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("payment_method", mode="before")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        valid = ["credit_card", "debit_card", "gift_card"]
        if value not in valid:
            raise ValueError(f"Payment method must be one of {valid}. Got '{value}'.")
        return value


class PlaceCafeOrderOutputModel(BaseModel):
    status: str = Field(..., description="The status of the ordering attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the ordering outcome.")
    order_id: Optional[str] = Field(default=None, description="The unique identifier for the newly created order.")
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax.")
    tax: Optional[float] = Field(default=None, description="Tax amount.")
    total_charged: Optional[float] = Field(default=None, description="The final total amount charged.")
    order_status: Optional[str] = Field(default=None, description="Current status of the order (e.g., 'Placed').")

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------
# Cancel Order
# -----------------------------------------------------------------------
class CancelCafeOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: str = Field(..., description="The unique identifier for the existing cafe order.")

    model_config = ConfigDict(extra="forbid")


class CancelCafeOrderOutputModel(BaseModel):
    status: str = Field(..., description="The status of the cancellation attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the cancellation outcome.")
    refund_status: Optional[str] = Field(default=None, description="Indicates the refund outcome.")
    refund_amount: Optional[float] = Field(default=None, description="The amount refunded to the user.")

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------
# Get Order
# -----------------------------------------------------------------------
class GetCafeOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: Optional[str] = Field(
        default=None,
        description="Optional. The specific order ID to retrieve. If not provided, retrieves all orders for the user.",
    )

    model_config = ConfigDict(extra="forbid")


class GetCafeOrderOutputModel(BaseModel):
    status: str = Field(..., description="The status of the retrieval attempt (e.g., 'success' or 'error').")
    message: str = Field(..., description="A descriptive message regarding the retrieval outcome.")
    orders: List[CafeOrder] = Field(default_factory=list, description="A list of matching orders.")

    model_config = ConfigDict(extra="forbid")
