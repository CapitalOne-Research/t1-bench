from t1_plus_plus.schema.dessert.dessert_order import (
    GetDessertOrderInputModel,
    GetDessertOrderOutputModel,
)
from t1_plus_plus.schema.dessert.dessert_order_db import global_dessert_orders_db


def get_dessert_order(**kwargs: GetDessertOrderInputModel) -> GetDessertOrderOutputModel:
    """
    Description:
        Retrieves dessert/bakery orders for a specific user.
        If an order_id is provided, it fetches that specific order.
        Otherwise, it returns all orders associated with the user_id.
    """
    try:
        input_data = GetDessertOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return GetDessertOrderOutputModel(status="error", message=f"Invalid input data: {str(e)}")

    matched_orders = []

    if input_data.order_id:
        order = global_dessert_orders_db.get_order(input_data.order_id)
        if order:
            if order.user_id == input_data.user_id:
                matched_orders.append(order)
            else:
                return GetDessertOrderOutputModel(
                    status="error",
                    message="Unauthorized access. This order does not belong to the provided user_id.",
                )
        else:
            return GetDessertOrderOutputModel(
                status="error",
                message=f"Order {input_data.order_id} not found.",
            )
    else:
        for order in global_dessert_orders_db.orders.values():
            if order.user_id == input_data.user_id:
                matched_orders.append(order)
        matched_orders.reverse()

    if not matched_orders:
        return GetDessertOrderOutputModel(status="success", message="No orders found for this user.", orders=[])

    return GetDessertOrderOutputModel(
        status="success",
        message=f"Successfully retrieved {len(matched_orders)} order(s).",
        orders=matched_orders,
    )
