from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    CancelReservationInputModel,
    CancelReservationOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_reservations_db


def cancel_food_and_dining_reservation(**kwargs) -> CancelReservationOutputModel:
    """
    Description:
        Cancel an existing dine-in reservation. Only Active reservations can be cancelled.
        A full refund of the reservation charge is issued on successful cancellation.

    Examples:
    >>> # Usage Example:
    cancel_food_and_dining_reservation(user_id="USR-DFEDBA29", reservation_id="RES-1A2946F9")

    Returns:
        CancelReservationOutputModel: status, message, refund_amount.
    """
    try:
        input_data = CancelReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    reservation = global_reservations_db.get_reservation(input_data.reservation_id)
    if not reservation:
        return CancelReservationOutputModel(
            status="error",
            message=f"Cancellation failed. Reservation {input_data.reservation_id} not found.",
        )

    if reservation.user_id != input_data.user_id:
        return CancelReservationOutputModel(
            status="error",
            message="Cancellation failed. You are not authorized to cancel this reservation.",
        )

    if reservation.status != "Active":
        return CancelReservationOutputModel(
            status="error",
            message=f"Cancellation failed. Only Active reservations can be cancelled. Current status: {reservation.status}.",
        )

    success = global_reservations_db.update_status(input_data.reservation_id, "Cancelled")
    if success:
        return CancelReservationOutputModel(
            status="success",
            message=f"Reservation {input_data.reservation_id} successfully cancelled. Full refund of ${reservation.reservation_charge:.2f} issued.",
            refund_amount=reservation.reservation_charge,
        )

    return CancelReservationOutputModel(
        status="error",
        message="An internal error occurred while cancelling the reservation.",
    )
