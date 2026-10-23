import pandas as pd
from pathlib import Path
import os

from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    OrderItem,
    ModifyDeliveryOrderInputModel,
    ModifyDeliveryOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_delivery_orders_db

_data_dir = Path(__file__).resolve().parents[4] / "datasets"
ALL_FOOD_AND_DINING_MENUS = os.getenv(
    "ALL_FOOD_AND_DINING_MENUS", str(_data_dir / "data_food_and_dining_menus.csv")
)

try:
    food_and_dining_menus_df = pd.read_csv(ALL_FOOD_AND_DINING_MENUS)
except FileNotFoundError:
    food_and_dining_menus_df = pd.DataFrame()

TAX_RATE = 0.07


def modify_food_and_dining_delivery_order(**kwargs) -> ModifyDeliveryOrderOutputModel:
    """
    Description:
        Modify an existing delivery order. Can update items, delivery address, payment methods,
        or special instructions. Only orders with status 'Placed' or 'Preparing' can be modified.

    Examples:
    >>> # Usage Example: Change delivery address
    modify_food_and_dining_delivery_order(user_id="USR-60F5438A", order_id="DO-A1B2C3D4", delivery_address="123 New St, Austin, TX 78701")

    >>> # Usage Example: Change items
    modify_food_and_dining_delivery_order(user_id="USR-BFEA9099", order_id="DO-E5F6A7B8", items=[{"item_id": "ITEM-0981", "quantity": 2}])

    Returns:
        ModifyDeliveryOrderOutputModel: status, order_id, total_charged, order_status.
    """
    try:
        input_data = ModifyDeliveryOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return ModifyDeliveryOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    order = global_delivery_orders_db.get_order(input_data.order_id)
    if not order:
        return ModifyDeliveryOrderOutputModel(
            status="error",
            message=f"Modification failed. Delivery order {input_data.order_id} not found.",
        )

    if order.user_id != input_data.user_id:
        return ModifyDeliveryOrderOutputModel(
            status="error",
            message="Modification failed. You are not authorized to modify this order.",
        )

    if order.status not in ["Placed", "Preparing"]:
        return ModifyDeliveryOrderOutputModel(
            status="error",
            message=f"Modification failed. Orders with status '{order.status}' cannot be modified.",
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
                return ModifyDeliveryOrderOutputModel(
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

    if input_data.delivery_address is not None:
        updates["delivery_address"] = input_data.delivery_address

    if input_data.payment_methods is not None:
        updates["payment_methods"] = input_data.payment_methods

    if input_data.special_instructions is not None:
        updates["special_instructions"] = input_data.special_instructions

    global_delivery_orders_db.update_order(input_data.order_id, **updates)

    return ModifyDeliveryOrderOutputModel(
        status="success",
        message=f"Delivery order {input_data.order_id} successfully modified. Total charged: ${new_total:.2f}.",
        order_id=input_data.order_id,
        total_charged=new_total,
        order_status=order.status,
    )
