from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Shared item models
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    """Represents a single line item in a pickup order."""

    item_id: str = Field(..., description="The unique identifier for the menu item.")
    quantity: int = Field(..., description="The number of this specific item ordered.")
    line_total: float = Field(..., description="The total cost for this line item (unit price × quantity).")


class OrderItemInput(BaseModel):
    """Represents a single item the agent wants to order."""

    item_id: str = Field(..., description="The unique identifier for the menu item.")
    quantity: int = Field(..., description="The number of this specific item ordered. Must be at least 1.")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Quantity must be at least 1.")
        return value


class MenuItem(BaseModel):
    """Represents a single menu item returned by get_food_and_dining_menu."""

    item_id: str = Field(..., description="Unique ID for the menu item, required for ordering.")
    item_name: str = Field(..., description="Name of the food item.")
    description: str = Field(..., description="Description of the item.")
    base_price: float = Field(..., description="Price of the item.")
    dietary_tags: List[str] = Field(default_factory=list, description="Dietary tags (e.g., 'vegan', 'halal').")
    allergens: List[str] = Field(default_factory=list, description="Allergens present (e.g., 'dairy', 'gluten').")


# ---------------------------------------------------------------------------
# Pickup order (fast food / quick-service)
# ---------------------------------------------------------------------------

class PlacePickupOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    restaurant_id: str = Field(..., description="The unique identifier for the restaurant location.")
    items: List[OrderItemInput] = Field(..., description="List of items to order, each with item_id and quantity.")
    payment_methods: List[str] = Field(
        ..., description="Payment methods (e.g., ['credit_cards', 'reward_points']). Max 2."
    )
    promo_code: Optional[str] = Field(default=None, description="Optional promo code (e.g., 'SAVE10' for 10% off).")

    model_config = ConfigDict(extra="forbid")

    @field_validator("payment_methods", mode="before")
    @classmethod
    def validate_payment_methods(cls, value: List[str]) -> List[str]:
        if len(value) == 0:
            raise ValueError("At least one payment method must be provided.")
        if len(value) > 2:
            raise ValueError("A maximum of two payment methods can be used per order.")
        return value


class PlacePickupOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    order_id: Optional[str] = Field(default=None, description="Unique ID for the newly created order.")
    total_charged: Optional[float] = Field(default=None, description="Final amount charged.")
    order_status: Optional[str] = Field(default=None, description="Current order status (e.g., 'Placed').")

    model_config = ConfigDict(extra="forbid")


class CancelPickupOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: str = Field(..., description="The unique identifier for the pickup order.")

    model_config = ConfigDict(extra="forbid")


class CancelPickupOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    refund_status: Optional[str] = Field(default=None, description="Refund outcome (e.g., 'Full Refund').")
    refund_amount: Optional[float] = Field(default=None, description="Amount refunded.")

    model_config = ConfigDict(extra="forbid")


class ModifyPickupOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: str = Field(..., description="The unique identifier for the pickup order to modify.")
    items: Optional[List[OrderItemInput]] = Field(default=None, description="Updated list of items. Replaces the existing items if provided.")
    payment_methods: Optional[List[str]] = Field(default=None, description="Updated payment methods. Max 2.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("payment_methods")
    @classmethod
    def validate_payment_methods(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None:
            if len(value) == 0:
                raise ValueError("At least one payment method must be provided.")
            if len(value) > 2:
                raise ValueError("A maximum of two payment methods can be used per order.")
        return value


class ModifyPickupOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    order_id: Optional[str] = Field(default=None, description="The pickup order ID.")
    total_charged: Optional[float] = Field(default=None, description="Updated total charge.")
    order_status: Optional[str] = Field(default=None, description="Current order status.")

    model_config = ConfigDict(extra="forbid")


class GetPickupOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: Optional[str] = Field(
        default=None,
        description="Optional. Specific order ID to retrieve. If omitted, returns all orders for the user.",
    )

    model_config = ConfigDict(extra="forbid")


class GetPickupOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    orders: list = Field(default_factory=list, description="List of matching orders.")

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Menu retrieval
# ---------------------------------------------------------------------------

class GetFoodAndDiningMenuInputModel(BaseModel):
    restaurant_id: str = Field(..., description="The unique identifier for the restaurant location.")

    model_config = ConfigDict(extra="forbid")


class GetFoodAndDiningMenuOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    restaurant_name: Optional[str] = Field(default=None, description="Name of the restaurant.")
    menu_items: List[MenuItem] = Field(default_factory=list, description="Available menu items.")

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Reservation
# ---------------------------------------------------------------------------

class BookReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    restaurant_id: str = Field(..., description="The unique identifier for the establishment.")
    primary_guest_name: str = Field(..., description="Name of the primary guest for the reservation.")
    number_guests: int = Field(..., description="Number of guests.")
    price_per_person: float = Field(..., description="Price per person charged for the reservation.")
    reservation_date: str = Field(..., description="Date of the reservation in YYYY-MM-DD format.")
    reservation_time: str = Field(..., description="Time of the reservation in HH:MM format (24-hour).")
    has_private_dining: bool = Field(default=False, description="Whether to upgrade to private dining (+$50.00 fee).")

    model_config = ConfigDict(extra="forbid")

    @field_validator("reservation_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("reservation_date must be in 'YYYY-MM-DD' format.")
        return value

    @field_validator("reservation_time", mode="before")
    @classmethod
    def validate_time(cls, value: Any) -> str:
        try:
            datetime.strptime(value, "%H:%M")
        except (ValueError, TypeError):
            raise ValueError("reservation_time must be in 'HH:MM' format.")
        return value

    @field_validator("number_guests")
    @classmethod
    def validate_guests(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Number of guests must be at least 1.")
        return value


class BookReservationOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    reservation_id: Optional[str] = Field(default=None, description="Unique ID for the reservation.")
    reservation_date: Optional[str] = Field(default=None, description="Date of the reservation (YYYY-MM-DD).")
    reservation_time: Optional[str] = Field(default=None, description="Time of the reservation (HH:MM).")
    reservation_charge: Optional[float] = Field(default=None, description="Total charge for the reservation.")
    has_private_dining: Optional[bool] = Field(default=None, description="Whether private dining was booked.")

    model_config = ConfigDict(extra="forbid")


class ModifyReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(..., description="The unique identifier for the existing reservation.")
    new_number_guests: Optional[int] = Field(default=None, description="Updated number of guests.")
    new_price_per_person: Optional[float] = Field(default=None, description="Updated price per person.")
    new_reservation_date: Optional[str] = Field(default=None, description="Updated date in YYYY-MM-DD format.")
    new_reservation_time: Optional[str] = Field(default=None, description="Updated time in HH:MM format (24-hour).")
    upgrade_private_dining: Optional[bool] = Field(
        default=None, description="Set to True to upgrade to private dining (+$50.00 fee)."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_number_guests")
    @classmethod
    def validate_guests(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("Number of guests must be at least 1.")
        return value

    @field_validator("new_reservation_date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("new_reservation_date must be in 'YYYY-MM-DD' format.")
        return value

    @field_validator("new_reservation_time", mode="before")
    @classmethod
    def validate_time(cls, value: Any) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
        except (ValueError, TypeError):
            raise ValueError("new_reservation_time must be in 'HH:MM' format.")
        return value


class ModifyReservationOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    reservation_id: Optional[str] = Field(default=None, description="Reservation ID.")
    reservation_date: Optional[str] = Field(default=None, description="Current reservation date (YYYY-MM-DD).")
    reservation_time: Optional[str] = Field(default=None, description="Current reservation time (HH:MM).")
    new_charge: Optional[float] = Field(default=None, description="Updated total reservation charge.")
    has_private_dining: Optional[bool] = Field(default=None, description="Whether private dining is active.")

    model_config = ConfigDict(extra="forbid")


class CancelReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: str = Field(..., description="The unique identifier for the reservation.")

    model_config = ConfigDict(extra="forbid")


class CancelReservationOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    refund_amount: Optional[float] = Field(default=None, description="Amount refunded.")

    model_config = ConfigDict(extra="forbid")


class GetReservationInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    reservation_id: Optional[str] = Field(
        default=None,
        description="Optional. Specific reservation ID to retrieve. If omitted, returns all reservations for the user.",
    )

    model_config = ConfigDict(extra="forbid")


class GetReservationOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    reservations: list = Field(default_factory=list, description="List of matching reservations.")

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Delivery order
# ---------------------------------------------------------------------------

class PlaceDeliveryOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    restaurant_id: str = Field(..., description="The unique identifier for the restaurant location.")
    delivery_address: str = Field(..., description="Full delivery address (street, city, state, zip).")
    items: List[OrderItemInput] = Field(..., description="List of items to order, each with item_id and quantity.")
    payment_methods: List[str] = Field(
        ..., description="Payment methods (e.g., ['Visa', 'reward_points']). Max 2."
    )
    special_instructions: Optional[str] = Field(
        default=None, description="Optional delivery or preparation instructions (e.g., 'Leave at door')."
    )
    promo_code: Optional[str] = Field(
        default=None, description="Optional promo code. 'SAVE10' gives 10% off subtotal; 'FREEDELIVERY' waives the delivery fee."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("payment_methods", mode="before")
    @classmethod
    def validate_payment_methods(cls, value: List[str]) -> List[str]:
        if len(value) == 0:
            raise ValueError("At least one payment method must be provided.")
        if len(value) > 2:
            raise ValueError("A maximum of two payment methods can be used per order.")
        return value


class PlaceDeliveryOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    order_id: Optional[str] = Field(default=None, description="Unique ID for the newly created delivery order.")
    total_charged: Optional[float] = Field(default=None, description="Final amount charged.")
    order_status: Optional[str] = Field(default=None, description="Current order status (e.g., 'Placed').")

    model_config = ConfigDict(extra="forbid")


class CancelDeliveryOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: str = Field(..., description="The unique identifier for the delivery order to cancel.")

    model_config = ConfigDict(extra="forbid")


class CancelDeliveryOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    refund_status: Optional[str] = Field(default=None, description="Refund outcome (e.g., 'Full Refund').")
    refund_amount: Optional[float] = Field(default=None, description="Amount refunded.")

    model_config = ConfigDict(extra="forbid")


class ModifyDeliveryOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: str = Field(..., description="The unique identifier for the delivery order to modify.")
    items: Optional[List[OrderItemInput]] = Field(default=None, description="Updated list of items. Replaces the existing items if provided.")
    delivery_address: Optional[str] = Field(default=None, description="Updated delivery address.")
    payment_methods: Optional[List[str]] = Field(default=None, description="Updated payment methods. Max 2.")
    special_instructions: Optional[str] = Field(default=None, description="Updated delivery or preparation instructions.")

    model_config = ConfigDict(extra="forbid")

    @field_validator("payment_methods")
    @classmethod
    def validate_payment_methods(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None:
            if len(value) == 0:
                raise ValueError("At least one payment method must be provided.")
            if len(value) > 2:
                raise ValueError("A maximum of two payment methods can be used per order.")
        return value


class ModifyDeliveryOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    order_id: Optional[str] = Field(default=None, description="The delivery order ID.")
    total_charged: Optional[float] = Field(default=None, description="Updated total charge.")
    order_status: Optional[str] = Field(default=None, description="Current order status.")

    model_config = ConfigDict(extra="forbid")


class GetDeliveryOrderInputModel(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    order_id: Optional[str] = Field(
        default=None,
        description="Optional. Specific delivery order ID to retrieve. If omitted, returns all delivery orders for the user.",
    )

    model_config = ConfigDict(extra="forbid")


class GetDeliveryOrderOutputModel(BaseModel):
    status: str = Field(..., description="'success' or 'error'.")
    message: str = Field(..., description="Outcome message.")
    orders: list = Field(default_factory=list, description="List of matching delivery orders.")

    model_config = ConfigDict(extra="forbid")
