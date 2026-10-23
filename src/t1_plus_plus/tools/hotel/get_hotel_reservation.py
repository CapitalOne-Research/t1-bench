from t1_plus_plus.schema.hotel.hotel_reservation import (
    GetHotelReservationInputModel,
    GetHotelReservationOutputModel,
)
from t1_plus_plus.schema.hotel.hotel_reservation_db import global_hotel_reservations_db


def get_hotel_reservation(**kwargs: GetHotelReservationInputModel) -> GetHotelReservationOutputModel:
    """
    Description:
        Retrieves hotel reservations for a specific user.
        If a reservation_id is provided, it fetches that specific reservation.
        Otherwise, it returns all reservations associated with the user_id.

    Examples:
    >>> # Usage Example: Fetching all reservations for a specific user
    get_hotel_reservation(user_id="user_123")

    >>> # Usage Example: Fetching a specific reservation for a user
    get_hotel_reservation(user_id="user_123", reservation_id="res_4567")

    Returns:
        GetHotelReservationOutputModel: Output object which contains the status of the operation, a descriptive message, and the resulting matched reservations.
    """
    # 1. Validate Agent Input
    try:
        input_data = GetHotelReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return GetHotelReservationOutputModel(
            status="error",
            message=f"Invalid input data: {str(e)}",
        )

    matched_reservations = []

    # 2. Case A: Fetch a specific reservation by reservation_id
    if input_data.reservation_id:
        reservation = global_hotel_reservations_db.get_reservation(input_data.reservation_id)
        if reservation:
            # Security check: Ensure the requested reservation actually belongs to this user
            if reservation.user_id == input_data.user_id:
                matched_reservations.append(reservation)
            else:
                return GetHotelReservationOutputModel(
                    status="error",
                    message="Unauthorized access. This reservation does not belong to the provided user_id.",
                )
        else:
            return GetHotelReservationOutputModel(
                status="error",
                message=f"Reservation {input_data.reservation_id} not found.",
            )

    # 3. Case B: Fetch all reservations for the user
    else:
        # Iterate through the in-memory database to find all reservations for this user
        for reservation in global_hotel_reservations_db.reservations.values():
            if reservation.user_id == input_data.user_id:
                matched_reservations.append(reservation)
        # Reverse to show the most recently added reservations first
        matched_reservations.reverse()

    # 4. Return results
    if not matched_reservations:
        return GetHotelReservationOutputModel(
            status="success", 
            message="No reservations found for this user.", 
            reservations=[]
        )

    return GetHotelReservationOutputModel(
        status="success", 
        message=f"Successfully retrieved {len(matched_reservations)} reservation(s).", 
        reservations=matched_reservations
    )