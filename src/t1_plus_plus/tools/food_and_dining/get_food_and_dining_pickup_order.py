from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    GetPickupOrderInputModel,
    GetPickupOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_pickup_orders_db


def get_food_and_dining_pickup_order(**kwargs) -> GetPickupOrderOutputModel:
    """
    Description:
        Retrieve pickup orders for a user. If an order_id is provided, fetches that specific order.
        Otherwise returns all orders for the user.

    Examples:
    >>> # Usage Example: All orders for a user
    get_food_and_dining_pickup_order(user_id="USR-60F5438A")

    >>> # Usage Example: Specific order
    get_food_and_dining_pickup_order(user_id="USR-60F5438A", order_id="PO-D35981C4")

    Returns:
        GetPickupOrderOutputModel: status, message, and list of matching orders.
    """
    try:
        input_data = GetPickupOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return GetPickupOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}", orders=[]
        )

    matched = []

    if input_data.order_id:
        order = global_pickup_orders_db.get_order(input_data.order_id)
        if not order:
            return GetPickupOrderOutputModel(
                status="error",
                message=f"Order {input_data.order_id} not found.",
                orders=[],
            )
        if order.user_id != input_data.user_id:
            return GetPickupOrderOutputModel(
                status="error",
                message="Unauthorized access. This order does not belong to the provided user_id.",
                orders=[],
            )
        matched.append(order.model_dump())
    else:
        for order in global_pickup_orders_db.orders.values():
            if order.user_id == input_data.user_id:
                matched.append(order.model_dump())
        matched.reverse()

    if not matched:
        return GetPickupOrderOutputModel(
            status="success", message="No orders found for this user.", orders=[]
        )

    return GetPickupOrderOutputModel(
        status="success",
        message=f"Successfully retrieved {len(matched)} order(s).",
        orders=matched,
    )
