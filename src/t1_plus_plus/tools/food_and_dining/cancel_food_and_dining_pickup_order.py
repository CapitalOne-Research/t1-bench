from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    CancelPickupOrderInputModel,
    CancelPickupOrderOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_pickup_orders_db


def cancel_food_and_dining_pickup_order(**kwargs) -> CancelPickupOrderOutputModel:
    """
    Description:
        Cancel an existing pickup order. Only orders with status 'Placed' can be cancelled.
        Orders that are 'Ready_for_Pickup' or 'Completed' cannot be cancelled.
        A full refund is issued on successful cancellation.

    Examples:
    >>> # Usage Example:
    cancel_food_and_dining_pickup_order(user_id="USR-60F5438A", order_id="PO-D35981C4")

    >>> # Usage Example:
    cancel_food_and_dining_pickup_order(user_id="USR-BFEA9099", order_id="PO-86310147")

    Returns:
        CancelPickupOrderOutputModel: status, refund_status, and refund_amount.
    """
    try:
        input_data = CancelPickupOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelPickupOrderOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    order = global_pickup_orders_db.get_order(input_data.order_id)
    if not order:
        return CancelPickupOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Order {input_data.order_id} not found.",
        )

    if order.user_id != input_data.user_id:
        return CancelPickupOrderOutputModel(
            status="error",
            message="Cancellation failed. You are not authorized to cancel this order.",
        )

    status = order.status

    if status == "Cancelled":
        return CancelPickupOrderOutputModel(
            status="error",
            message=f"Order {input_data.order_id} has already been cancelled.",
        )

    if status in ["Ready_for_Pickup", "Completed"]:
        return CancelPickupOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Orders with status '{status}' cannot be cancelled.",
        )

    if status == "Placed":
        success = global_pickup_orders_db.update_order_status(input_data.order_id, "Cancelled")
        if success:
            return CancelPickupOrderOutputModel(
                status="success",
                message=f"Order {input_data.order_id} successfully cancelled.",
                refund_status="Full Refund",
                refund_amount=order.total,
            )
        return CancelPickupOrderOutputModel(
            status="error",
            message="An internal error occurred while cancelling the order.",
        )

    return CancelPickupOrderOutputModel(
        status="error",
        message=f"Cannot cancel order with current status: {status}.",
    )
