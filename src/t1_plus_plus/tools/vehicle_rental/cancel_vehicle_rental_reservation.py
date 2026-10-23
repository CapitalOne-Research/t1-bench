from datetime import datetime, timedelta
from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation import (
    CancelRentalReservationInputModel,
    CancelRentalReservationOutputModel,
)
from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation_db import (
    global_rental_reservations_db,
)


def cancel_vehicle_rental_reservation(
    **kwargs: CancelRentalReservationInputModel,
) -> CancelRentalReservationOutputModel:
    """
    Description:
        Cancels a rental. Checks the 24-hour window (latest_refund_date_days)
        to determine refund status vs late penalty.

    Examples:
    >>> # Usage Example:
    cancel_vehicle_rental_reservation(user_id="U123", reservation_id="REN-AB12CD34", reason="Found alternative transport")

    >>> # Usage Example:
    cancel_vehicle_rental_reservation(user_id="U456", reservation_id="REN-EF56GH78", reason="Trip cancelled")

    Returns:
        CancelRentalReservationOutputModel: Output object containing status, message, refund_status, fee_charged, and reason_logged.
    """
    input_data = CancelRentalReservationInputModel.model_validate(kwargs)

    res = global_rental_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelRentalReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return CancelRentalReservationOutputModel(
            status="error", message="User ID does not match the reservation record."
        )

    if res.status == "Cancelled":
        return CancelRentalReservationOutputModel(
            status="error", message="Reservation is already cancelled."
        )

    # Refund Logic: Based on start_date
    time_until_pickup = res.start_date - datetime.now()
    cutoff_timedelta = timedelta(days=res.latest_refund_date_days)

    refund_status = "Full Refund"
    fee_charged = 0.0

    if time_until_pickup < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = 50.00  # Standard late fee for rentals

    res.status = "Cancelled"

    global_rental_reservations_db.add_reservation(res)

    return CancelRentalReservationOutputModel(
        status="success",
        message="Rental reservation successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged,
        reason_logged=input_data.reason,
    )
