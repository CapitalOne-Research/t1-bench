from t1_plus_plus.schema.cafe.cafe_order import (
    CancelCafeOrderInputModel,
    CancelCafeOrderOutputModel,
)
from t1_plus_plus.schema.cafe.cafe_order_db import global_cafe_orders_db


def cancel_cafe_order(**kwargs: CancelCafeOrderInputModel) -> CancelCafeOrderOutputModel:
    """
    Description:
        Cancels an existing cafe order. Validates if the order belongs to the user
        and if the current order status allows for cancellation (must be 'Placed').
    """
    try:
        input_data = CancelCafeOrderInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelCafeOrderOutputModel(status="error", message=f"Invalid input data: {str(e)}")

    order = global_cafe_orders_db.get_order(input_data.order_id)

    if not order:
        return CancelCafeOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Order {input_data.order_id} not found.",
        )

    if order.user_id != input_data.user_id:
        return CancelCafeOrderOutputModel(
            status="error",
            message="Cancellation failed. You are not authorized to cancel this order.",
        )

    if order.status == "Cancelled":
        return CancelCafeOrderOutputModel(
            status="error",
            message=f"Order {input_data.order_id} has already been cancelled.",
        )

    if order.status in ["Preparing", "Ready_for_Pickup", "Completed"]:
        return CancelCafeOrderOutputModel(
            status="error",
            message=f"Cancellation failed. Orders with status '{order.status}' cannot be cancelled.",
        )

    if order.status == "Placed":
        success = global_cafe_orders_db.update_order_status(input_data.order_id, "Cancelled")
        if success:
            return CancelCafeOrderOutputModel(
                status="success",
                message=f"Order {input_data.order_id} successfully cancelled.",
                refund_status="Full Refund",
                refund_amount=order.total,
            )
        else:
            return CancelCafeOrderOutputModel(
                status="error",
                message="An internal database error occurred while trying to cancel the order.",
            )

    return CancelCafeOrderOutputModel(
        status="error",
        message=f"Cannot cancel order with current status: {order.status}.",
    )
