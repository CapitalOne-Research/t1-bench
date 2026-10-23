from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    GetDeliveryOrderInputModel,
    GetDeliveryOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_delivery_orders_db


def get_food_and_dining_delivery_order(**kwargs) -> GetDeliveryOrderOutputModel:
    """
    Description:
        Retrieve delivery orders for a user. If an order_id is provided, fetches that specific
        delivery order. Otherwise returns all delivery orders for the user.

    Examples:
    >>> # Usage Example: All delivery orders for a user
    get_food_and_dining_delivery_order(user_id="USR-60F5438A")

    >>> # Usage Example: Specific delivery order
    get_food_and_dining_delivery_order(user_id="USR-BFEA9099", order_id="DO-E5F6A7B8")

    Returns:
        GetDeliveryOrderOutputModel: status, message, and list of matching delivery orders.
    """
    try:
        input_data = GetDeliveryOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return GetDeliveryOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}", orders=[]
        )

    matched = []

    if input_data.order_id:
        order = global_delivery_orders_db.get_order(input_data.order_id)
        if not order:
            return GetDeliveryOrderOutputModel(
                status="error",
                message=f"Delivery order {input_data.order_id} not found.",
                orders=[],
            )
        if order.user_id != input_data.user_id:
            return GetDeliveryOrderOutputModel(
                status="error",
                message="Unauthorized access. This order does not belong to the provided user_id.",
                orders=[],
            )
        matched.append(order.model_dump())
    else:
        for order in global_delivery_orders_db.orders.values():
            if order.user_id == input_data.user_id:
                matched.append(order.model_dump())
        matched.reverse()

    if not matched:
        return GetDeliveryOrderOutputModel(
            status="success", message="No delivery orders found for this user.", orders=[]
        )

    return GetDeliveryOrderOutputModel(
        status="success",
        message=f"Successfully retrieved {len(matched)} delivery order(s).",
        orders=matched,
    )
