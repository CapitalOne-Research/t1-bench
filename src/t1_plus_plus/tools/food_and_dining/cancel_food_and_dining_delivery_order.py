from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    CancelDeliveryOrderInputModel,
    CancelDeliveryOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_delivery_orders_db


def cancel_food_and_dining_delivery_order(**kwargs) -> CancelDeliveryOrderOutputModel:
    """
    Description:
        Cancel an existing delivery order. Only orders with status 'Placed' or 'Preparing' can be
        cancelled. Orders that are 'Out_for_Delivery', 'Delivered', or already 'Cancelled' cannot
        be cancelled. A full refund is issued on successful cancellation.

    Examples:
    >>> # Usage Example:
    cancel_food_and_dining_delivery_order(user_id="USR-60F5438A", order_id="DO-A1B2C3D4")

    >>> # Usage Example:
    cancel_food_and_dining_delivery_order(user_id="USR-BFEA9099", order_id="DO-E5F6A7B8")

    Returns:
        CancelDeliveryOrderOutputModel: status, refund_status, and refund_amount.
    """
    try:
        input_data = CancelDeliveryOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelDeliveryOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    order = global_delivery_orders_db.get_order(input_data.order_id)
    if not order:
        return CancelDeliveryOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Delivery order {input_data.order_id} not found.",
        )

    if order.user_id != input_data.user_id:
        return CancelDeliveryOrderOutputModel(
            status="error",
            message="Cancellation failed. You are not authorized to cancel this order.",
        )

    status = order.status

    if status == "Cancelled":
        return CancelDeliveryOrderOutputModel(
            status="error",
            message=f"Delivery order {input_data.order_id} has already been cancelled.",
        )

    if status in ["Out_for_Delivery", "Delivered"]:
        return CancelDeliveryOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Orders with status '{status}' cannot be cancelled.",
        )

    if status in ["Placed", "Preparing"]:
        success = global_delivery_orders_db.update_order_status(input_data.order_id, "Cancelled")
        if success:
            return CancelDeliveryOrderOutputModel(
                status="success",
                message=f"Delivery order {input_data.order_id} successfully cancelled.",
                refund_status="Full Refund",
                refund_amount=order.total,
            )
        return CancelDeliveryOrderOutputModel(
            status="error",
            message="An internal error occurred while cancelling the order.",
        )

    return CancelDeliveryOrderOutputModel(
        status="error",
        message=f"Cannot cancel delivery order with current status: {status}.",
    )
