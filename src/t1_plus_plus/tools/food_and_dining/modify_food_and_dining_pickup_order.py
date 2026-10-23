import pandas as pd
from pathlib import Path
import os

from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    OrderItem,
    ModifyPickupOrderInputModel,
    ModifyPickupOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_pickup_orders_db

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FOOD_AND_DINING_MENUS = os.getenv(
    "ALL_FOOD_AND_DINING_MENUS", str(_data_dir / "data_food_and_dining_menus.csv")
)

try:
    food_and_dining_menus_df = pd.read_csv(ALL_FOOD_AND_DINING_MENUS)
except FileNotFoundError:
    food_and_dining_menus_df = pd.DataFrame()

TAX_RATE = 0.07


def modify_food_and_dining_pickup_order(**kwargs) -> ModifyPickupOrderOutputModel:
    """
    Description:
        Modify an existing pickup order. Can update the items or payment methods.
        Only orders with status 'Placed' can be modified.

    Examples:
    >>> # Usage Example: Change items
    modify_food_and_dining_pickup_order(user_id="USR-60F5438A", order_id="PO-D35981C4", items=[{"item_id": "ITEM-4036", "quantity": 2}])

    >>> # Usage Example: Change payment method
    modify_food_and_dining_pickup_order(user_id="USR-BFEA9099", order_id="PO-86310147", payment_methods=["Visa"])

    Returns:
        ModifyPickupOrderOutputModel: status, order_id, total_charged, order_status.
    """
    try:
        input_data = ModifyPickupOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return ModifyPickupOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    order = global_pickup_orders_db.get_order(input_data.order_id)
    if not order:
        return ModifyPickupOrderOutputModel(
            status="error",
            message=f"Modification failed. Order {input_data.order_id} not found.",
        )

    if order.user_id != input_data.user_id:
        return ModifyPickupOrderOutputModel(
            status="error",
            message="Modification failed. You are not authorized to modify this order.",
        )

    if order.status != "Placed":
        return ModifyPickupOrderOutputModel(
            status="error",
            message=f"Modification failed. Only orders with status 'Placed' can be modified. Current status: '{order.status}'.",
        )

    updates = {}

    if input_data.items is not None:
        location_menus = food_and_dining_menus_df[
            food_and_dining_menus_df["restaurant_id"] == order.restaurant_id
        ]
        subtotal = 0.0
        final_items = []
        for item_req in input_data.items:
            item_match = location_menus[location_menus["item_id"] == item_req.item_id]
            if item_match.empty:
                return ModifyPickupOrderOutputModel(
                    status="error",
                    message=f"Modification failed. Item {item_req.item_id} is not available at this location.",
                )
            menu_item = item_match.iloc[0]
            unit_price = float(menu_item["base_price"])
            line_total = round(unit_price * item_req.quantity, 2)
            subtotal += line_total
            final_items.append(
                OrderItem(item_id=item_req.item_id, quantity=item_req.quantity, line_total=line_total)
            )
        tax = round(subtotal * TAX_RATE, 2)
        new_total = round(subtotal + tax, 2)
        updates["items"] = [i.model_dump() for i in final_items]
        updates["total"] = new_total
    else:
        new_total = order.total

    if input_data.payment_methods is not None:
        updates["payment_methods"] = input_data.payment_methods

    global_pickup_orders_db.update_order(input_data.order_id, **updates)

    return ModifyPickupOrderOutputModel(
        status="success",
        message=f"Pickup order {input_data.order_id} successfully modified. Total charged: ${new_total:.2f}.",
        order_id=input_data.order_id,
        total_charged=new_total,
        order_status=order.status,
    )
