import hashlib
import os
from pathlib import Path

import pandas as pd

from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    OrderItem,
    PlaceDeliveryOrderInputModel,
    PlaceDeliveryOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import (
    DeliveryOrder,
    global_delivery_orders_db,
)
from t1_plus_plus.ontology.food_and_dining import (
    DELIVERY_TAX_RATE,
    DELIVERY_FEE,
    REWARD_POINTS_TO_DOLLAR,
)

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FOOD_AND_DINING = os.getenv("ALL_FOOD_AND_DINING", str(_data_dir / "data_food_and_dining.csv"))
ALL_FOOD_AND_DINING_MENUS = os.getenv(
    "ALL_FOOD_AND_DINING_MENUS", str(_data_dir / "data_food_and_dining_menus.csv")
)
ALL_USERS = os.getenv("ALL_COMBINED_USERS", str(_data_dir / "data_combined_users.csv"))

try:
    food_and_dining_df = pd.read_csv(ALL_FOOD_AND_DINING)
    food_and_dining_menus_df = pd.read_csv(ALL_FOOD_AND_DINING_MENUS)
    users_df = pd.read_csv(ALL_USERS)
except FileNotFoundError:
    food_and_dining_df = pd.DataFrame()
    food_and_dining_menus_df = pd.DataFrame()
    users_df = pd.DataFrame()


def place_food_and_dining_delivery_order(**kwargs) -> PlaceDeliveryOrderOutputModel:
    """
    Description:
        Place a new delivery order at a food and dining establishment that supports delivery.
        Validates items against the location's menu, calculates the total (subtotal + delivery fee
        + 8% tax), applies a promo code if provided (SAVE10 gives 10% off subtotal; FREEDELIVERY
        waives the $4.99 delivery fee), and handles reward points deduction (100 points = $1.00).
        Supports up to two payment methods per order.

    Examples:
    >>> # Usage Example: Single item with delivery address
    place_food_and_dining_delivery_order(user_id="USR-60F5438A", restaurant_id="FAD-112822", delivery_address="123 Main St, Norfolk, VA 23510", items=[{"item_id": "ITEM-41636", "quantity": 2}], payment_methods=["Solana"])

    >>> # Usage Example: Multiple items with free delivery promo
    place_food_and_dining_delivery_order(user_id="USR-0BEDC644", restaurant_id="FAD-223875", delivery_address="456 Oak Ave, North Charleston, SC 29405", items=[{"item_id": "ITEM-107241", "quantity": 1}], payment_methods=["Diners Club"], promo_code="FREEDELIVERY")

    >>> # Usage Example: With special instructions and two payment methods
    place_food_and_dining_delivery_order(user_id="USR-BFEA9099", restaurant_id="FAD-220718", delivery_address="789 Elm St, Tallahassee, FL 32301", items=[{"item_id": "ITEM-53486", "quantity": 1}], payment_methods=["Visa", "Ethereum"], special_instructions="Leave at door, ring bell")

    Returns:
        PlaceDeliveryOrderOutputModel: status, order_id, total_charged, and order_status.
    """
    try:
        input_data = PlaceDeliveryOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return PlaceDeliveryOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    # Verify restaurant exists and supports delivery
    if food_and_dining_df.empty or input_data.restaurant_id not in food_and_dining_df["id"].values:
        return PlaceDeliveryOrderOutputModel(
            status="error",
            message=f"Order failed. Establishment with ID {input_data.restaurant_id} not found.",
        )

    rest_row = food_and_dining_df[food_and_dining_df["id"] == input_data.restaurant_id].iloc[0]
    if str(rest_row.get("supports_delivery", "False")).lower() != "true":
        return PlaceDeliveryOrderOutputModel(
            status="error",
            message=f"Order failed. Establishment {input_data.restaurant_id} does not support delivery.",
        )

    # Validate and price items
    location_menus = food_and_dining_menus_df[
        food_and_dining_menus_df["restaurant_id"] == input_data.restaurant_id
    ]

    subtotal = 0.0
    final_order_items = []

    for item_req in input_data.items:
        item_match = location_menus[location_menus["item_id"] == item_req.item_id]
        if item_match.empty:
            return PlaceDeliveryOrderOutputModel(
                status="error",
                message=f"Order failed. Item {item_req.item_id} is not available at this location.",
            )

        menu_item = item_match.iloc[0]
        if "is_available" in menu_item and str(menu_item["is_available"]).lower() == "false":
            return PlaceDeliveryOrderOutputModel(
                status="error",
                message=f"Order failed. {menu_item['item_name']} is currently sold out.",
            )

        unit_price = float(menu_item["base_price"])
        line_total = round(unit_price * item_req.quantity, 2)
        subtotal += line_total
        final_order_items.append(
            OrderItem(item_id=item_req.item_id, quantity=item_req.quantity, line_total=line_total)
        )

    # Apply promo code
    promo_discount = 0.0
    delivery_fee = DELIVERY_FEE
    if input_data.promo_code:
        code = input_data.promo_code.upper()
        if code == "SAVE10":
            promo_discount = round(subtotal * 0.10, 2)
            subtotal = round(subtotal - promo_discount, 2)
        elif code == "FREEDELIVERY":
            delivery_fee = 0.0
        else:
            return PlaceDeliveryOrderOutputModel(
                status="error",
                message=f"Order failed. Promo code '{input_data.promo_code}' is invalid.",
            )

    tax = round(subtotal * DELIVERY_TAX_RATE, 2)
    total_amount = round(subtotal + tax + delivery_fee, 2)
    final_charge = total_amount
    points_used = 0

    # Apply reward points
    if "reward_points" in input_data.payment_methods:
        if users_df.empty or input_data.user_id not in users_df["user_id"].values:
            return PlaceDeliveryOrderOutputModel(
                status="error",
                message=f"Order failed. User {input_data.user_id} not found.",
            )
        user_row = users_df[users_df["user_id"] == input_data.user_id].iloc[0]
        points_balance = int(user_row.get("reward_points_balance", 0))
        points_value = points_balance / REWARD_POINTS_TO_DOLLAR

        if points_value >= final_charge:
            points_used = int(final_charge * REWARD_POINTS_TO_DOLLAR)
            final_charge = 0.0
        else:
            if len(input_data.payment_methods) == 1:
                return PlaceDeliveryOrderOutputModel(
                    status="error",
                    message=(
                        f"Order failed. Reward points balance ({points_balance} pts = ${points_value:.2f}) "
                        f"is insufficient to cover the total (${total_amount:.2f}). "
                        "Please add a second payment method (e.g., 'credit_cards')."
                    ),
                )
            points_used = points_balance
            final_charge = round(total_amount - points_value, 2)

    item_seed = ":".join(sorted(f"{i.item_id}x{i.quantity}" for i in input_data.items))
    payment_seed = ":".join(sorted(input_data.payment_methods))
    seed = f"{input_data.user_id}:{input_data.restaurant_id}:{input_data.delivery_address}:{item_seed}:{payment_seed}"
    order_id = f"DO-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"

    new_order = DeliveryOrder(
        order_id=order_id,
        user_id=input_data.user_id,
        restaurant_id=input_data.restaurant_id,
        delivery_address=input_data.delivery_address,
        items=[item.model_dump() for item in final_order_items],
        special_instructions=input_data.special_instructions,
        payment_methods=input_data.payment_methods,
        promo_code=input_data.promo_code,
        total=final_charge,
        status="Placed",
    )

    global_delivery_orders_db.add_order(new_order)

    return PlaceDeliveryOrderOutputModel(
        status="success",
        message=f"Delivery order placed successfully. Total charged: ${final_charge:.2f}. Points used: {points_used}.",
        order_id=order_id,
        total_charged=final_charge,
        order_status="Placed",
    )
