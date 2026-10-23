from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    GetReservationInputModel,
    GetReservationOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_reservations_db


def get_food_and_dining_reservation(**kwargs) -> GetReservationOutputModel:
    """
    Description:
        Retrieve dine-in reservations for a user. If a reservation_id is provided, fetches that
        specific reservation. Otherwise returns all reservations for the user.

    Examples:
    >>> # Usage Example: All reservations for a user
    get_food_and_dining_reservation(user_id="USR-DFEDBA29")

    >>> # Usage Example: Specific reservation
    get_food_and_dining_reservation(user_id="USR-DFEDBA29", reservation_id="RES-1A2946F9")

    Returns:
        GetReservationOutputModel: status, message, and list of matching reservations.
    """
    try:
        input_data = GetReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return GetReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}", reservations=[]
        )

    matched = []

    if input_data.reservation_id:
        reservation = global_reservations_db.get_reservation(input_data.reservation_id)
        if not reservation:
            return GetReservationOutputModel(
                status="error",
                message=f"Reservation {input_data.reservation_id} not found.",
                reservations=[],
            )
        if reservation.user_id != input_data.user_id:
            return GetReservationOutputModel(
                status="error",
                message="Unauthorized access. This reservation does not belong to the provided user_id.",
                reservations=[],
            )
        matched.append(reservation.model_dump())
    else:
        for reservation in global_reservations_db.reservations.values():
            if reservation.user_id == input_data.user_id:
                matched.append(reservation.model_dump())
        matched.reverse()

    if not matched:
        return GetReservationOutputModel(
            status="success", message="No reservations found for this user.", reservations=[]
        )

    return GetReservationOutputModel(
        status="success",
        message=f"Successfully retrieved {len(matched)} reservation(s).",
        reservations=matched,
    )
