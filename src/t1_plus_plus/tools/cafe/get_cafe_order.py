from t1_plus_plus.schema.cafe.cafe_order import (
    GetCafeOrderInputModel,
    GetCafeOrderOutputModel,
)
from t1_plus_plus.schema.cafe.cafe_order_db import global_cafe_orders_db


def get_cafe_order(**kwargs: GetCafeOrderInputModel) -> GetCafeOrderOutputModel:
    """
    Description:
        Retrieves cafe orders for a specific user.
        If an order_id is provided, it fetches that specific order.
        Otherwise, it returns all orders associated with the user_id.
    """
    try:
        input_data = GetCafeOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return GetCafeOrderOutputModel(status="error", message=f"Invalid input data: {str(e)}")

    matched_orders = []

    if input_data.order_id:
        order = global_cafe_orders_db.get_order(input_data.order_id)
        if order:
            if order.user_id == input_data.user_id:
                matched_orders.append(order)
            else:
                return GetCafeOrderOutputModel(
                    status="error",
                    message="Unauthorized access. This order does not belong to the provided user_id.",
                )
        else:
            return GetCafeOrderOutputModel(
                status="error",
                message=f"Order {input_data.order_id} not found.",
            )
    else:
        for order in global_cafe_orders_db.orders.values():
            if order.user_id == input_data.user_id:
                matched_orders.append(order)
        matched_orders.reverse()

    if not matched_orders:
        return GetCafeOrderOutputModel(status="success", message="No orders found for this user.", orders=[])

    return GetCafeOrderOutputModel(
        status="success",
        message=f"Successfully retrieved {len(matched_orders)} order(s).",
        orders=matched_orders,
    )
