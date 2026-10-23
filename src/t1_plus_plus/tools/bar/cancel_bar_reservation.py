from datetime import datetime, timedelta

from t1_plus_plus.schema.bar.bar_reservation import (
    CancelBarReservationInputModel,
    CancelBarReservationOutputModel,
)
from t1_plus_plus.schema.bar.bar_reservation_db import global_bar_reservations_db


def cancel_bar_reservation(
    **kwargs: CancelBarReservationInputModel,
) -> CancelBarReservationOutputModel:
    """
    Description:
        Use this tool to cancel an existing bar reservation. Checks the 48-hour threshold to determine if the user receives a full refund or is charged a base cancellation fee.

    Examples:
    >>> # Usage Example:
    cancel_bar_reservation(user_id="U123", reservation_id="RES-ABC12345")

    >>> # Usage Example:
    cancel_bar_reservation(user_id="U789", reservation_id="RES-DEF67890", reason="Change of plans")

    Returns:
        CancelBarReservationOutputModel: Output object which contains the cancellation status, refund status, fee charged, and logged reason.
    """
    input_data = CancelBarReservationInputModel.model_validate(kwargs)

    # Retrieve from global db
    res = global_bar_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return CancelBarReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return CancelBarReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status == "Cancelled":
        return CancelBarReservationOutputModel(
            status="error", message="Reservation is already cancelled."
        )

    time_until_event = res.event_datetime - datetime.now()
    cutoff_timedelta = timedelta(days=res.latest_refund_date_days)

    refund_status = "Full Refund"
    fee_charged = 0.0

    if time_until_event < cutoff_timedelta:
        refund_status = "Late Cancellation Fee Applied"
        fee_charged = 25.00  # Base fee charged for late cancellation

    res.status = "Cancelled"

    # Re-save to ensure the DB registers the updated Pydantic object
    global_bar_reservations_db.add_reservation(res)

    return CancelBarReservationOutputModel(
        status="success",
        message="Reservation successfully cancelled.",
        refund_status=refund_status,
        fee_charged=fee_charged,
        reason_logged=input_data.reason,
    )
