from datetime import datetime, timedelta

from t1_plus_plus.schema.live_show.live_show_reservation import (
    CancelLiveShowReservationInputModel,
    CancelLiveShowReservationOutputModel,
)
from t1_plus_plus.schema.live_show.live_show_reservation_db import global_show_reservations_db

def cancel_live_show_reservation(**kwargs: CancelLiveShowReservationInputModel) -> CancelLiveShowReservationOutputModel:
    """
    Description:
        Use this tool to cancel an existing show reservation. Checks the refund threshold (based on the reservation's latest_refund_date_days) to determine if the user receives a full refund or is charged a $25 late cancellation fee.

    Examples:
    >>> # Usage Example:
    cancel_live_show_reservation(user_id="user_123", reservation_id="SHOW-A1B2C3D4", reason="Change of plans.")

    >>> # Usage Example:
    cancel_live_show_reservation(user_id="user_456", reservation_id="SHOW-E5F6G7H8", reason="Unable to attend due to scheduling conflict.")

    Returns:
        CancelLiveShowReservationOutputModel: Output object which contains the cancellation status, message, refund status, and any fee charged.
    """
    input_data = CancelLiveShowReservationInputModel.model_validate(kwargs)

    # 1. Retrieve the reservation from the global database
    res = global_show_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelLiveShowReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    # 2. Ownership and Status Checks
    if res.user_id != input_data.user_id:
        return CancelLiveShowReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status == "Cancelled":
        return CancelLiveShowReservationOutputModel(
            status="error", message="Reservation is already cancelled."
        )

    # 3. Calculate Time Until Event and Refund Status
    time_until_event = res.event_datetime - datetime.now()
    cutoff_timedelta = timedelta(days=res.latest_refund_date_days)

    refund_status = "Full Refund"
    fee_charged = 0.0

    # If the current time is within the late cancellation window
    if time_until_event < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = 25.00  # Standard fee for late show cancellations

    # 4. Update Status and Persist
    res.status = "Cancelled"
    global_show_reservations_db.add_reservation(res)

    return CancelLiveShowReservationOutputModel(
        status="success",
        message="Reservation successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged,
    )