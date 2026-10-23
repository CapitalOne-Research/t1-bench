from datetime import datetime, timedelta
from t1_plus_plus.schema.cruise.cruise_reservation import (
    CancelCruiseReservationInputModel,
    CancelCruiseReservationOutputModel,
)
from t1_plus_plus.schema.cruise.cruise_reservation_db import global_cruise_reservations_db

def cancel_cruise_reservation(**kwargs: CancelCruiseReservationInputModel) -> CancelCruiseReservationOutputModel:
    """
    Description:
        Cancels a cruise reservation. Checks the 14-day threshold (latest_refund_date_days)
        to determine if the user gets a full refund or is charged a cancellation fee.
    """
    # 2. Validate Agent Input with Error Catching
    try:
        input_data = CancelCruiseReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return CancelCruiseReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    res = global_cruise_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelCruiseReservationOutputModel(status="error", message="Reservation ID not found.")

    if res.user_id != input_data.user_id:
        return CancelCruiseReservationOutputModel(status="error", message="User ID does not match the reservation.")

    if res.status == "Cancelled":
        return CancelCruiseReservationOutputModel(status="error", message="Reservation is already cancelled.")

    time_until_departure = res.departure_date - datetime.now()
    cutoff_timedelta = timedelta(days=res.latest_refund_date_days)

    refund_status = "Full Refund"
    fee_charged = 0.0

    if time_until_departure < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = 250.00  # Higher base fee charged for late cruise cancellation

    res.status = "Cancelled"
    global_cruise_reservations_db.add_reservation(res)

    return CancelCruiseReservationOutputModel(
        status="success",
        message="Cruise reservation successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged,
        reason_logged=input_data.reason,
    )
