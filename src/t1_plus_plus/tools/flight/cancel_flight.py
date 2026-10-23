from datetime import datetime, timedelta
from t1_plus_plus.schema.flight.flight_reservation import (
    CancelFlightReservationInputModel,
    CancelFlightReservationOutputModel,
)
from t1_plus_plus.schema.flight.flight_reservation_db import global_flight_reservations_db

def cancel_flight(**kwargs: CancelFlightReservationInputModel) -> CancelFlightReservationOutputModel:
    """
    Description:
        Cancels a flight reservation. Checks the 7-day threshold (latest_refund_date_days)
        to determine if the user gets a full refund or is charged a cancellation fee.

    Examples:
    >>> # Usage Example:
    cancel_flight(user_id="user_123", reservation_id="RES-ABC12345", reason="Change of plans")

    >>> # Usage Example:
    cancel_flight(user_id="user_456", reservation_id="RES-DEF67890", reason="Medical emergency")

    Returns:
        CancelFlightReservationOutputModel: Output object containing cancellation status, refund outcome, and any fee charged.
    """
    input_data = CancelFlightReservationInputModel.model_validate(kwargs)
    res = global_flight_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelFlightReservationOutputModel(status="error", message="Reservation ID not found.")

    if res.user_id != input_data.user_id:
        return CancelFlightReservationOutputModel(status="error", message="User ID does not match the reservation.")

    if res.status == "Cancelled":
        return CancelFlightReservationOutputModel(status="error", message="Reservation is already cancelled.")

    time_until_departure = res.departure_date - datetime.now()
    cutoff_timedelta = timedelta(days=res.latest_refund_date_days)

    refund_status = "Full Refund"
    fee_charged = 0.0

    if time_until_departure < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = 150.00  # Late cancellation fee for flights

    res.status = "Cancelled"
    global_flight_reservations_db.add_reservation(res)

    return CancelFlightReservationOutputModel(
        status="success",
        message="Flight reservation successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged,
        reason_logged=input_data.reason,
    )
