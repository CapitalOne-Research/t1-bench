from typing import Any

from t1_plus_plus.schema.kayak.cancel_kayak_reservation import CancelKayakReservationInputModel, CancelKayakReservationOutputModel
from t1_plus_plus.schema.kayak.kayak_reservation_db import global_kayak_reservation_db


def cancel_kayak_reservation(**kwargs: Any) -> CancelKayakReservationOutputModel:
    """
    Cancels an existing kayak reservation and issues a simplified 100% full refund.
    """
    try:
        cancel_data = CancelKayakReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelKayakReservationOutputModel(
            status="error", message=f"Validation error: {str(e)}"
        )

    # 1. Fetch the reservation from the DB
    reservation = global_kayak_reservation_db.get_reservation(cancel_data.booking_id)

    if not reservation:
        return CancelKayakReservationOutputModel(
            status="error", message=f"No reservation found with ID {cancel_data.booking_id}."
        )

    # 2. Verify User ID matches
    if reservation.user_id != cancel_data.user_id:
        return CancelKayakReservationOutputModel(
            status="error", message="User ID does not match the reservation owner."
        )

    # 3. Check if already cancelled
    if reservation.status == "Cancelled":
        return CancelKayakReservationOutputModel(
            status="error", message="This reservation is already cancelled."
        )

    # 4. Apply 100% Refund (Simplified Logic)
    refund_status = "Full Refund"
    refund_amount = reservation.total_cost

    # 5. Update the Database
    success = global_kayak_reservation_db.update_reservation_status(cancel_data.booking_id, "Cancelled")

    if not success:
        return CancelKayakReservationOutputModel(
            status="error", message="Failed to update database status."
        )

    return CancelKayakReservationOutputModel(
        status="success",
        message=f"Reservation {cancel_data.booking_id} has been cancelled successfully. Reason logged: {cancel_data.reason}",
        refund_status=refund_status,
        refund_amount=refund_amount
    )
